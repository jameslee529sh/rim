from typing import List, Tuple, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

import aqi_db as adb
import security
import rim


app = FastAPI()

# 允许跨域
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],    # allow all other web servers CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/securities")
def read_securities():
    return {"hello world": security.get_securities(adb.get_securities)}


@app.get("/profit-forecast/")
def read_profit_forecast(code: str):
    return {f"{code} profit forecast": rim.get_profit_forecast(code, adb.get_profit_forecast)}


@app.get("/financial-indicator/")
def read_indicator2018(code: str):
    return {f"{code} 2018 financial indicator": rim.get_indicator2018(code, adb.get_indicator2018)}


class RE(BaseModel):
    rr: float                       # required return, 必要投资报酬率 / 折现率
    gr: float                       # growth rate，持续期的剩余收益增长率
    value: float                    # 对企业的剩余收益估值
    discounted_re2019: float        # 折现后的2019年剩余收益
    discounted_re2020: float        # 折现后的2020年剩余收益
    discounted_re2021: float        # 折现后的2021年剩余收益
    discounted_cv: float            # # 折现后的持续期剩余收益


class RIMValue(BaseModel):
    bps2018: float                  # 2018年每股净资产
    rr: List[float]
    gr: List[float]
    re: List[RE]                    # 不同假设下的剩余收益


@app.get("/rim-value/", response_model=RIMValue)
def read_rim_value(code: str):
    return rim.calculate_rim_value(code)


@app.get("/profitability/8yr-roe/")
def read_years_roe(code: str):
    return profit_ability.calculate_yrs_roe(code)


class MGMSValue(BaseModel):
    code: str
    mm: int                 # maximum margin, MM = max(mg rank, ms rank)，最大盈利能力指标
    mg: float               # margin growth, MG = (II(1 + ΔGM / GM)) ^ 1/T - 1，盈利能力成长性指标
    mg_rank: int            # rank of mg, 盈利能力成长性在全市场的百分位
    ms: float               # margin stability, MS = AVG(GM) / STD(GM), 盈利能力稳定性指标
    ms_rank: int            # rank of ms, 盈利能力稳定性在全市场的百分位


@app.get("/profitability/mg-ms", response_model=MGMSValue)
def read_years_roe(code: str):
    return profit_ability.get_mg_ms(code)


class RIMProposal(BaseModel):
    code: str
    capital_return_rate_range: Tuple[float, float] = (0.07, 0.13)
    capital_return_rate_default: float = 0.10
    analysis_eps: List[Tuple[str, Optional[float]]] = [('2019', 1.1), ('2020', 1.3), ('2021', 1.4)]
    t1_range: Tuple[int, int] = (5, 7)
    t1_t2: int = 12
    g1_range: Tuple[float, float] = (0.00, 0.60)
    g1_default: float = 0.10
    last_bps: Tuple[str, float] = ('2018', 8.12)
    last_eps: Tuple[str, float] = ('2018', 1.0)
    industry_roe: float = 0.12
    g2_range: Tuple[float, float] = (0.00, 0.04)
    g2_default: float = 0.02


@app.get("/v1.0/rim-proposal", response_model=RIMProposal)
def read_rim_proposal(code: str):
    p = rim.build_rim_proposal(code)
    return {'code': code, 'industry_roe': p.industry_roe,
            'analysis_eps': [('2019', p.eps_2019), ('2020', p.eps_2020), ('2021 ', p.eps_2021)],
            'last_bps': ('2018', p.bps_2018), 'last_eps': ('2018', p.eps_2018)}


class PublicCompanyInfo(BaseModel):
    code: str
    market_value: float                 # 市值，单位~亿元
    industry: str                       # 行业
    main_business: str                  # 主营业务
    registered_place: str               # 注册地
    history: List[str] = ['To Do', ]                 # 上市历史


@app.get("/v1.0/a_public_company_info", response_model=PublicCompanyInfo)
def read_a_public_company_info(code: str):
    market_value = adb.get_market_value()(code)
    company_info = adb.get_company_info()(code)
    return {'code': code,
            'market_value': market_value.market_cap,
            'industry': company_info.industry_1 + '/' + company_info.industry_2,
            'main_business': company_info.main_business,
            'registered_place': company_info.province + '/' + company_info.city
                if company_info.province not in ['重庆', '上海', '北京', '天津'] else company_info.province}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
    # uvicorn.run(app, host="172.19.217.132", port=80)
