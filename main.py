import math
import re
from typing import List

import companynameparser
import pandas as pd
from loguru import logger
from tqdm import tqdm

from app.client import SearchEngine
from app.schemas.company import CompanyDocument
from app.utils import load_data

c = CompanyDocument(corp_id="11", corp_cn_name="123")


collection_name = "corp"

engine = SearchEngine()


def engine_data_init():
    fields = [
        {"name": "corp_id", "type": "string"},
        {
            "name": "corp_cn_name",
            "type": "string",
            "locale": "zh",
            "facet": False,
            "index": True,
        },
    ]
    engine.create_collection(collection_name, fields)
    target_data = load_data("./data/sample/target_corp.csv")
    data = target_data.to_dict("records")
    engine.import_data(collection_name, data)


def load_file_match(src_files: List[str]):
    results = []
    src_files = src_files
    for src_file in tqdm(src_files, desc="Prcessing file"):
        df = load_data(src_file, sep=";")
        df = df[["SRC_CORP_ID", "CORP_CN_NAME", "SRC_ID", "SRC_REC_ID"]].rename(
            columns={
                "SRC_CORP_ID": "corp_id",
                "CORP_CN_NAME": "corp_cn_name",
                "SRC_ID": "src_id",
                "SRC_REC_ID": "src_rec_id",
            }
        )
        src_corps = df.to_dict("records")
        for src_corp in tqdm(src_corps, desc="Processing source corp"):
            src_corp_cn_name = src_corp["corp_cn_name"]
            # logger.info(f'match on {src_corp["corp_cn_name"]}')
            src_parse = companynameparser.parse(
                src_corp_cn_name, pos_sensitive=False, enable_word_segment=True
            )
            src_brand = re.sub("[,-]", "", src_parse["brand"])
            if src_brand == "":
                continue
            page = 1
            total_page = 1
            while page <= total_page:
                # logger.info(f"{page=} {total_page=} {src_parse=}")
                try:
                    query_result = engine.query(
                        collection_name=collection_name,
                        query_by="corp_cn_name",
                        q=src_brand,
                        page=page,
                    )
                except:
                    query_result = engine.query(
                        collection_name=collection_name,
                        query_by="corp_cn_name",
                        q=src_brand,
                        page=page,
                    )
                documents = query_result["hits"]
                total_page = math.ceil(query_result["found"] / 100)
                if total_page >= 1000:
                    logger.warning(
                        f'match on  {src_corp["corp_cn_name"]} need do something'
                    )
                    page = total_page + 1
                else:
                    page += 1
                for doc in documents:
                    corp_info = doc["document"]
                    corp_id = corp_info["corp_id"]
                    corp_cn_name = corp_info["corp_cn_name"]
                    targ_parse = companynameparser.parse(
                        corp_cn_name, pos_sensitive=False, enable_word_segment=True
                    )
                    if targ_parse["brand"] == src_parse["brand"] and set(
                        src_parse["trade"].split(",")
                    ).intersection(set(targ_parse["trade"].split(","))):
                        corp_match = {
                            "src_corp_id": src_corp["corp_id"],
                            "src_corp_name": src_corp["corp_cn_name"],
                            "corp_id": corp_info["corp_id"],
                            "corp_cn_name": corp_info["corp_cn_name"],
                            "src_id": src_corp["src_id"],
                            "src_rec_id": src_corp["src_rec_id"],
                        }
                        results.append(corp_match)
        df = pd.DataFrame(results)
        df.to_csv("./data/output/result_1.csv", index=False, encoding="utf-8")
    return results


def main():
    results = load_file_match(
        ["./data/sample/src_data1.csv", "./data/sample/src_data2.csv"]
    )
    df = pd.DataFrame(results)
    print(df.info())
    print(df.head())
    df.to_csv("./data/output/result.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
