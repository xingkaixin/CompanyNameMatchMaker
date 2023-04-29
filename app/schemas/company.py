from pydantic import BaseModel


class CompanyDocument(BaseModel):
    corp_id: str
    corp_cn_name: str
