import pandas as pd
import json
import os


def clean_telecom_capacity_json():
    input_file = os.path.join(os.path.dirname(__file__), "分省电信主要通行能力_多年期_原始抓取.csv")
    if not os.path.exists(input_file):
        print(f"找不到文件: {input_file}")
        return

    df_raw = pd.read_csv(input_file)
    print(f"成功读取原始数据，共有 {len(df_raw)} 条记录。开始解析...")

    all_records = []

    for _, row in df_raw.iterrows():
        prov_name = row["省份名称"]
        prov_code = row["省份代码"]
        raw_json_str = row["JSON数据"]

        try:
            data_dict = json.loads(raw_json_str)

            if not data_dict.get("success", False):
                print(f"省份 {prov_name} 的 JSON 数据无效: {data_dict.get('message', '')}")
                continue

            year_data_list = data_dict.get("data", [])

            for yd in year_data_list:
                year_str = yd.get("name", "")
                year_int = int(year_str.replace("年", "")) if "年" in year_str else year_str

                row_data = {
                    "省辖市代码": prov_code,
                    "省份": prov_name,
                    "年份": year_int
                }

                indicators = yd.get("values", [])
                for ind in indicators:
                    ind_name = ind.get("i_showname", "").strip()
                    val = ind.get("value", "")

                    try:
                        val_float = float(val) if val != "" else pd.NA
                    except ValueError:
                        val_float = pd.NA

                    row_data[ind_name] = val_float

                all_records.append(row_data)

        except Exception as e:
            print(f"解析 {prov_name} 时发生错误: {e}")

    df_clean = pd.DataFrame(all_records)
    df_clean.dropna(how="all", axis=1, inplace=True)
    df_clean.sort_values(by=["省辖市代码", "年份"], ascending=[True, False], inplace=True)

    output_file = os.path.join(os.path.dirname(__file__), "分省电信主要通行能力_多年期_面板数据.csv")
    df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\n清洗完成，最终面板数据共有 {len(df_clean)} 行。")
    print(f"已保存至: {output_file}")


if __name__ == "__main__":
    clean_telecom_capacity_json()
