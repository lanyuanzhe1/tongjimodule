import requests
import json
import time
import random
import pandas as pd
import os


def fetch_telecom_capacity_data():
    # 国家统计局数据接口
    url = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/getEsDataByCidAndDt"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Client_info": "eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoxMSwicGxhdGZvcm0iOiJXaW4zMiIsImlzV2VidmlldyI6ZmFsc2UsImlzQm90IjpmYWxzZSwidmVyc2lvbiI6IjE0Ny4wLjAuMCIsImNvcmUiOiJDaHJvbWUiLCJjb3JlVmVyc2lvbiI6IjE0Ny4wLjAuMCJ9",
        "Cookie": "_trs_uv=mo6xoqoy_6267_d4x5; client_info=eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoiMTAuMCIsInBsYXRmb3JtIjoiV2luMzIiLCJpc1dlYnZpZXciOmZhbHNlLCJpc0JvdCI6ZmFsc2UsInZlcnNpb24iOiIxNDcuMC4wLjAiLCJjb3JlIjoiQ2hyb21lIiwiY29yZVZlcnNpb24iOiIxNDcuMC4wLjAifQ==; JSESSIONID=8F417DB19FEBFB3B33C1ABB851A4C85D"
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
        "d15865ee03794ebf90fb10b891f0f6a2",
        "3ec01e328ac042989853adb05e599e2d",
        "be7a93aab27c46ce942ffe35ad8ace31",
        "61a91dcac2aa4165952a52c3d768946b",
        "8957c62ac22a44d88b82151aa7cb8f97"
    ]

    results = []
    print(f"开始抓取省份电信主要通行能力数据，涵盖 {len(provinces)} 个省市...")

    for prov_code, prov_name in provinces.items():
        print(f"正在获取 [{prov_name}] 数据...")

        payload = {
            "cid": "9c6547e43eac440cbca087f403e804ca",
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

    output_path = os.path.join(os.path.dirname(__file__), "分省电信主要通行能力_多年期_原始抓取.csv")
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n抓取完成，日志已写入 {output_path}")


if __name__ == "__main__":
    import urllib3

    urllib3.disable_warnings()
    fetch_telecom_capacity_data()
