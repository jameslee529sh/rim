from functools import lru_cache
from typing import Callable, NamedTuple, Tuple
from collections import namedtuple

import pandas as pd
import numpy as np

import aqi_db


RimProposal = namedtuple('RimProposal', ['code', 'bps_2018', 'eps_2018', 'industry_roe',
                                         'eps_2019', 'eps_2020', 'eps_2021'])


def _is_A_list_company_symbol(code: str) -> bool:
    """测试code是否是符合A股代码要求的字符串
    Precondition
    =======================================================================================
    :param code: A股代码

    Post condition
    =======================================================================================
    :return: True or False

    Examples:
    =======================================================================================
    >>> _is_A_list_company_symbol('300072')
    True

    >>> _is_A_list_company_symbol(300072)
    Traceback (most recent call last):
    ...
    AssertionError

    >>> _is_A_list_company_symbol('300072.SZ')
    False

    >>> _is_A_list_company_symbol('700072.SZ')
    False
    """
    assert isinstance(code, str)
    return code.isdigit() \
           and len(code) == 6 \
           and code[:3] in ('000', '002', '300', '600', '601', '603', '608', '688')


@lru_cache(maxsize=4096)
def build_rim_proposal(code: str,
                       get_indicator: Callable[[str], pd.DataFrame] = aqi_db.get_indicator,
                       get_eps_forecast: Callable[[str], pd.DataFrame] = aqi_db.get_profit_forecast,
                       fn_sw2_code: Callable[[str], str] = aqi_db.get_sw_industry(),
                       fn_industry_roe: Callable[[str], Tuple[str, str, float]] = aqi_db.get_sw_industry_roe()) \
        -> NamedTuple:
    """ 构建用于计算RIM的建议数据

    Precondition
    ===================================================================================
    :param code: 符合A股上市公司代码的要求
    :param get_indicator: 函数，返回DataFrame，index是上市公司代码，包含bps,eps列
    :param get_eps_forecast: 函数，返回DataFrame，index是上市公司代码，包含eps_2019, eps_2020, eps_2021列
    :param fn_sw2_code: 函数，输入上市公司代码，返回其申万二级行业代码
    :param fn_industry_roe: 函数, 输入参数是行业指数，返回元组（行业代码，行业名称，行业净资产收益率）

    Post condition
    ===================================================================================
    :return: 若某个股票没有eps预测值，则返回零
    """
    assert _is_A_list_company_symbol(code)

    is_nan = lambda x: 0 if np.isnan(x) else x

    code_indicator = get_indicator('2018').loc[code]
    code_eps_forecast = get_eps_forecast('2020-03-12').loc[code]
    return RimProposal(code=code, bps_2018=code_indicator['bps'], eps_2018=code_indicator['eps'],
                       industry_roe=fn_industry_roe(fn_sw2_code(code))[2],
                       eps_2019=is_nan(code_eps_forecast['eps_2019']),
                       eps_2020=is_nan(code_eps_forecast['eps_2020']),
                       eps_2021=is_nan(code_eps_forecast['eps_2021']))


if __name__ == "__main__":
    import doctest
    # doctest.testmod()
    print(build_rim_proposal('000625'))
