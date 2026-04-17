import requests
import json
import time
import random
import pandas as pd
import os

def fetch_population_data():
    # 国家统计局数据接口 (注意：这里是以 getEsDataByCidAndDt 为例)
    url = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/getEsDataByCidAndDt"
    
    # 强烈建议在此处补上你浏览器中的 Cookie 和 Client_info
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        # 请从网络面板中复制你自己的 Client_info
        "Client_info": "eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoxMSwicGxhdGZvcm0iOiJXaW4zMiIsImlzV2VidmlldyI6ZmFsc2UsImlzQm90IjpmYWxzZSwidmVyc2lvbiI6IjE0Ni4wLjAuMCIsImNvcmUiOiJDaHJvbWUiLCJjb3JlVmVyc2lvbiI6IjE0Ni4wLjAuMCJ9",
       
        "Cookie": "_trs_uv=mnlgbcdb_6267_946; client_info=eyJkZXZpY2UiOiJQQyIsImxhbmd1YWdlIjoiemhfQ04iLCJlbmdpbmUiOiJCbGluayIsImJyb3dzZXIiOiJFZGdlIiwib3MiOiJXaW5kb3dzIiwib3NWZXJzaW9uIjoiMTAuMCIsInBsYXRmb3JtIjoiV2luMzIiLCJpc1dlYnZpZXciOmZhbHNlLCJpc0JvdCI6ZmFsc2UsInZlcnNpb24iOiIxNDYuMC4wLjAiLCJjb3JlIjoiQ2hyb21lIiwiY29yZVZlcnNpb24iOiIxNDYuMC4wLjAifQ==; JSESSIONID=8B033B37D7141C2EE56252CE6479C930"
    }

    # 各省国标代码
    provinces = {
        "110000000000": "北京市", "120000000000": "天津市", "130000000000": "河北省", "140000000000": "山西省", "150000000000": "内蒙古自治区",
        "210000000000": "辽宁省", "220000000000": "吉林省", "230000000000": "黑龙江省", "310000000000": "上海市", "320000000000": "江苏省",
        "330000000000": "浙江省", "340000000000": "安徽省", "350000000000": "福建省", "360000000000": "江西省", "370000000000": "山东省",
        "410000000000": "河南省", "420000000000": "湖北省", "430000000000": "湖南省", "440000000000": "广东省", "450000000000": "广西壮族自治区",
        "460000000000": "海南省", "500000000000": "重庆市", "510000000000": "四川省", "520000000000": "贵州省", "530000000000": "云南省",
        "540000000000": "西藏自治区", "610000000000": "陕西省", "620000000000": "甘肃省", "630000000000": "青海省", "640000000000": "宁夏回族自治区",
        "650000000000": "新疆维吾尔自治区"
    }

    results = []
    print(f"开始抓取省份人口数据，涵盖 {len(provinces)} 个省市...")

    for prov_code, prov_name in provinces.items():
        print(f"正在获取 [{prov_name}] 数据...")
        
        # 动态替换 payload 里的 `das` 参数，确保按照循环拉取每一个省的数据
        payload = {
            "cid": "755d5f6efbcf41a6a411ad819aa93c17",
            "indicatorIds": [
                "4810ad6e9ddc41fc804a66134afe587f", 
                "1cca167b5743463886f3c18e4a4ae934", 
                "019c928598b44bb7a5fb52d8a9485175"
            ],
            "daCatalogId": "",
            "das": [{"text": prov_name, "value": prov_code}],
            "showType": "1",
            "dts": "",  # 留空以拉取全部年份，或者填入你自己测试的 ["2021YY-2025YY"]
            "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e"
        }

        try:
            # 发起POST请求 (关闭自签名证书的验证以防被拦截)
            res = requests.post(url, headers=headers, json=payload, verify=False, timeout=15)
            res.raise_for_status()
            data = res.json()
            
            # 将获取到的 JSON 返回原样存储
            results.append({
                "省份名称": prov_name,
                "省份代码": prov_code,
                "JSON数据": json.dumps(data, ensure_ascii=False)
            })
            
            # 防止被封禁，随机休眠
            time.sleep(random.uniform(2.0, 4.0))
            
        except Exception as e:
            print(f"❌ 请求 {prov_name} 时失败: {e}")
            break

    # 保存原始抓取数据到 0412 文件夹下
    output_path = os.path.join(os.path.dirname(__file__), "分省人口_多年期_原始抓取.csv")
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ 各省人口批量下载完成，日志已写入 {output_path}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    fetch_population_data()
