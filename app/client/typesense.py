from typing import Any, Dict, List

import typesense
from loguru import logger
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)


class SearchEngine:
    def __init__(self):
        self.client = typesense.Client(
            {
                "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
                "api_key": "xyz",
            }
        )

    def create_collection(
        self, collection_name: str, fields: List[Dict[str, Any]]
    ) -> None:
        try:
            self.client.collections[collection_name].retrieve()
            logger.info(f"collection name {collection_name} is exists will recreate")
            self.client.collections[collection_name].delete()
        except:
            logger.info(f"collection name {collection_name} is not exist will create")
        finally:
            logger.info(f"collection name {collection_name} creating")
            schema = {"name": collection_name, "fields": fields}
            self.client.collections.create(schema)
            logger.info(f"collection name {collection_name} created")

    def import_data(self, collection_name: str, data: List[Dict[str, str]]) -> None:
        self.client.collections[COLLECTION_NAME].documents.import_(data)

    @retry(
        wait=wait_fixed(1),
        stop=stop_after_attempt(2),
    )
    def query(
        self,
        collection_name: str,
        query_by: str,
        q: str,
        page: int = 1,
        per_page: int = 250,
    ):
        query_result = self.client.collections[collection_name].documents.search(
            {
                "pre_segmented_query": True,
                "query_by": query_by,
                "q": q,
                "per_page": per_page,
                "page": page,
            }
        )
        return query_result
