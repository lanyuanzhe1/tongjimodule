import requests
import json
import time
import random
import pandas as pd
import os


def fetch_energy_production_data():
    # 国家统计局数据接口
    url = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/getEsDataByCidAndDt"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Client_info": "eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoxMSwicGxhdGZvcm0iOiJXaW4zMiIsImlzV2VidmlldyI6ZmFsc2UsImlzQm90IjpmYWxzZSwidmVyc2lvbiI6IjE0Ny4wLjAuMCIsImNvcmUiOiJDaHJvbWUiLCJjb3JlVmVyc2lvbiI6IjE0Ny4wLjAuMCJ9",
        "Cookie": "_trs_uv=mo6xoqoy_6267_d4x5; client_info=eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoiMTAuMCIsInBsYXRmb3JtIjoiV2luMzIiLCJpc1dlYnZpZXciOmZhbHNlLCJpc0JvdCI6ZmFsc2UsInZlcnNpb24iOiIxNDcuMC4wLjAiLCJjb3JlIjoiQ2hyb21lIiwiY29yZVZlcnNpb24iOiIxNDcuMC4wLjAifQ==; JSESSIONID=7A1A9D798C5EDBE8F1BE53AB929C1FD8"
    }

    provinces = {
        "110000000000": "北京市", "120000000000": "天津市", "130000000000": "河北省", "140000000000": "山西省", "150000000000": "内蒙古自治区",
        "210000000000": "辽宁省", "220000000000": "吉林省", "230000000000": "黑龙江省", "310000000000": "上海市", "320000000000": "江苏省",
        "330000000000": "浙江省", "340000000000": "安徽省", "350000000000": "福建省", "360000000000": "江西省", "370000000000": "山东省",
        "410000000000": "河南省", "420000000000": "湖北省", "430000000000": "湖南省", "440000000000": "广东省", "450000000000": "广西壮族自治区",
        "460000000000": "海南省", "500000000000": "重庆市", "510000000000": "四川省", "520000000000": "贵州省", "530000000000": "云南省",
        "540000000000": "西藏自治区", "610000000000": "陕西省", "620000000000": "甘肃省", "630000000000": "青海省", "640000000000": "宁夏回族自治区",
        "650000000000": "新疆维吾尔自治区"
    }

    indicator_ids = [
        "c6d2f8d7af2941639c8a2e68f791cc5b",
        "dae0822572e142ae902b15b1fda7b34a",
        "e6988461352d448ca17e44c929a2d642",
        "d9ec8e5658b340218e2fe54a34a5d2b8",
        "225395e72cd44674a067820082a45a54",
        "b53b58d294f2447cb16551d78633cced",
        "76de8e81d432469c977d7693dbffb697",
        "df1221c66aef40c5bc82bb1024eff1d1",
        "eafb7863b41d471e9d5c8a58d4aa3531",
        "da02dfca04f94670b6506d071c52e053"
    ]

    results = []
    print(f"开始抓取省份主要能源产品产量数据，涵盖 {len(provinces)} 个省市...")

    for prov_code, prov_name in provinces.items():
        print(f"正在获取 [{prov_name}] 数据...")

        payload = {
            "cid": "ade19f093ebe43a5a773087039c5fedc",
            "indicatorIds": indicator_ids,
            "daCatalogId": "",
            "das": [{"text": prov_name, "value": prov_code}],
            "showType": "1",
            "dts": "",
            "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e"
        }

        try:
            res = requests.post(url, headers=headers, json=payload, verify=False, timeout=20)
            res.raise_for_status()
            data = res.json()

            results.append({
                "省份名称": prov_name,
                "省份代码": prov_code,
                "JSON数据": json.dumps(data, ensure_ascii=False)
            })

            time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            print(f"请求 {prov_name} 时失败: {e}")
            break

    output_path = os.path.join(os.path.dirname(__file__), "分省主要能源产品产量_多年期_原始抓取.csv")
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n抓取完成，日志已写入 {output_path}")


if __name__ == "__main__":
    import urllib3

    urllib3.disable_warnings()
    fetch_energy_production_data()
