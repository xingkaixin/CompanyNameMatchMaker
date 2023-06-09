import concurrent.futures
import math
import re
from pathlib import Path
from typing import Any, Dict, List

import addressparser
import companynameparser
import pandas as pd
from loguru import logger
from tqdm import tqdm

from app.client import SearchEngine
from app.utils import load_data, rating

collection_name = "corp"

engine = SearchEngine()


def trans_address(input_address: str) -> str:
    if input_address == "":
        return ("", "", "")
    try:
        df = addressparser.transform([input_address.encode("utf-8")])
    except:
        return ("", "", "")
    return (
        df.to_dict("records")[0]["省"],
        df.to_dict("records")[0]["市"],
        df.to_dict("records")[0]["区"],
    )


def search_engine_data_init():
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


def processing_corp(src_corp: Dict[str, Any]):
    results = []
    src_corp_cn_name = src_corp["corp_cn_name"]
    # logger.info(f'match on {src_corp["corp_cn_name"]}')
    src_parse = companynameparser.parse(
        src_corp_cn_name, pos_sensitive=False, enable_word_segment=True
    )
    src_brand = re.sub("[,-]", "", src_parse["brand"])
    # 非正常数据
    if src_brand == "":
        return results
    # 自然人
    if (
        src_brand not in ["人民政府"]
        and src_parse["trade"] == ""
        and src_parse["suffix"] == ""
    ):
        return results
    page = 1
    total_page = 1
    while page <= total_page:
        # logger.info(f"{page=} {total_page=} {src_parse=}")
        query_result = engine.query(
            collection_name=collection_name,
            query_by="corp_cn_name",
            q=f"{src_brand}",
            page=page,
        )
        documents = query_result["hits"]
        total_page = math.ceil(query_result["found"] / 100)
        if total_page >= 1000:
            logger.warning(f'match on  {src_corp["corp_cn_name"]} need do something')
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
            src_parse["place"] = trans_address(src_parse["place"])
            targ_parse["place"] = trans_address(targ_parse["place"])
            if rating(src_parse, targ_parse) >= 9.3:
                corp_match = {
                    "src_corp_id": src_corp["corp_id"],
                    "src_corp_name": src_corp["corp_cn_name"],
                    "corp_id": corp_info["corp_id"],
                    "corp_cn_name": corp_info["corp_cn_name"],
                    "src_id": src_corp["src_id"],
                    "src_rec_id": src_corp["src_rec_id"],
                    "rating": rating(src_parse, targ_parse),
                }
                results.append(corp_match)
    return results


def load_file_match_test(src_files: List[str]):
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

        executor = concurrent.futures.ProcessPoolExecutor(5)
        futures = [executor.submit(processing_corp, row) for _, row in df.iterrows()]
        results = []
        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Processing",
        ):
            results.append(future.result())
        executor.shutdown()
        df["search"] = results
        # tqdm.pandas()
        # df["search"] = df.progress_apply(lambda row: processing_corp(row), axis=1)
        df = df[df["search"].str.len() > 0]
        df.to_pickle(f"./data/output/{Path(src_file).name}.pkl")


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
        # for src_corp in tqdm(src_corps, desc="Processing source corp"):
        with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
            _results = list(
                tqdm(executor.map(processing_corp, src_corps), total=len(src_corps))
            )
            for i in _results:
                if len(i) == 0:
                    pass
                else:
                    for j in i:
                        results.append(j)

        df = pd.DataFrame(results)
        df.to_csv(f"./data/output/{Path(src_file).name}", index=False, encoding="utf-8")
    return results


def main():
    results = load_file_match(
        ["./data/sample/src_data1.csv", "./data/sample/src_data2.csv"]
    )
    df = pd.DataFrame(results)
    df.to_csv("./data/output/result.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
