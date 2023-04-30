from decimal import Decimal
from typing import Any, Dict


class ScoreBoard:
    def __init__(self):
        self._score: Decimal = Decimal(0.0)

    def __call__(self, score: float):
        self._score += Decimal(score)

    @property
    def score(self):
        return float(round(self._score, 1))


def rating(src: Dict[str, Any], targ: Dict[str, Any]) -> float:
    sb = ScoreBoard()
    # 品牌
    if src["brand"] == targ["brand"]:
        sb(8.0)
    # 行业
    if set(src["trade"].split(",")).intersection(set(targ["trade"].split(","))):
        sb(1.0)
    # 所在地
    # TODO 公司名称可能没有所在地，可以通过公司信息表获取所在地做补充
    src_province, src_city, src_district = src["place"]
    targ_province, targ_city, targ_district = targ["place"]
    if src_province != "" and src_province == targ_province:
        sb(0.4)
    if src_city != "" and src_city == targ_city:
        sb(0.3)
    if src_district != "" and src_district == targ_district:
        sb(0.3)
    if src_province == "" and targ_province == "":
        sb(0.2)
    if src_city == "" and targ_city == "":
        sb(0.1)
    if src_district == "" and targ_district == "":
        sb(0.1)

    return sb.score
