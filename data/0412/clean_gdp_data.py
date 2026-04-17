import pandas as pd
import json
import os

def clean_gdp_json():
    # 1. 读取刚刚抓取到的原始数据
    input_file = os.path.join(os.path.dirname(__file__), "分省GDP_多年期_原始抓取.csv")
    if not os.path.exists(input_file):
        print(f"❌ 找不到文件: {input_file}")
        return
        
    df_raw = pd.read_csv(input_file)
    print(f"✅ 成功读取原始数据，共有 {len(df_raw)} 条记录。开始解析...")

    all_records = []

    # 2. 逐行解析 JSON 结构
    for idx, row in df_raw.iterrows():
        prov_name = row['省份名称']
        prov_code = row['省份代码']
        raw_json_str = row['JSON数据']
        
        try:
            data_dict = json.loads(raw_json_str)
            
            # 判断返回值是否成功
            if not data_dict.get("success", False):
                print(f"⚠️ 省份 {prov_name} 的 JSON 数据似乎无效：{data_dict.get('message', '')}")
                continue
                
            # 拿到主要的年份数据列表
            year_data_list = data_dict.get("data", [])
            
            for yd in year_data_list:
                year_str = yd.get("name", "")  # 例如 "2024年"
                year_int = int(year_str.replace("年", "")) if "年" in year_str else year_str
                
                # 初始化这一年的基础面板行
                row_data = {
                    "省辖市代码": prov_code,
                    "省份": prov_name,
                    "年份": year_int
                }
                
                # 遍历该年份下的所有指标
                indicators = yd.get("values", [])
                for ind in indicators:
                    # 获取指标名称并清理多余的空格
                    ind_name = ind.get("i_showname", "").strip()
                    val = ind.get("value", "")
                    
                    # 转为浮点数，如果是空字符串或是 "--" 等无法转换的保留为空值
                    try:
                        val_float = float(val) if val != "" else pd.NA
                    except ValueError:
                        val_float = pd.NA
                        
                    row_data[ind_name] = val_float
                    
                all_records.append(row_data)
                
        except Exception as e:
            print(f"❌ 解析 {prov_name} 时发生错误: {e}")

    # 3. 转换为 DataFrame 宽表（Panel Data格式）
    df_clean = pd.DataFrame(all_records)

    # 清理掉全为空值的列
    df_clean.dropna(how='all', axis=1, inplace=True)
    
    # 按照省份和年份排序
    df_clean.sort_values(by=["省辖市代码", "年份"], ascending=[True, False], inplace=True)

    # 4. 导出
    output_file = os.path.join(os.path.dirname(__file__), "分省GDP_多年期_面板数据.csv")
    df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\n🎉 清洗完成！最终面板数据共有 {len(df_clean)} 行，包含字段：")
    for col in df_clean.columns:
        print(f"  - {col}")
    print(f"已保存至：{output_file}")

if __name__ == "__main__":
    clean_gdp_json()
