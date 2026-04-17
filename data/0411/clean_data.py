import os
import pandas as pd
import numpy as np

FOLDER_PATH = r'e:\code\tongjimodule\data\0411'

def parse_nbs_format(file_path):
    df_raw = pd.read_excel(file_path, header=None)
    
    # 找到所有的 '地区：'
    region_idx_list = df_raw.index[df_raw[0].astype(str).str.startswith('地区：')].tolist()
    if not region_idx_list:
        return pd.DataFrame()
        
    all_data = []
    
    for i, start_idx in enumerate(region_idx_list):
        region_name = str(df_raw.iloc[start_idx, 0]).replace('地区：', '').strip()
        end_idx = region_idx_list[i+1] if i + 1 < len(region_idx_list) else len(df_raw)
        
        df_region = df_raw.iloc[start_idx:end_idx].reset_index(drop=True)
        
        # 寻找'指标'行
        indicator_row = df_region[df_region[0] == '指标'].index
        if len(indicator_row) == 0:
            continue
        indicator_row_idx = indicator_row[0]
        
        years_arr = df_region.iloc[indicator_row_idx, 1:].values
        
        # 提取有效数字年份
        valid_cols = []
        valid_years = []
        for col_idx, y in enumerate(years_arr):
            y_str = str(y).replace('年', '').replace('.0', '').strip()
            if y_str.isdigit():
                valid_cols.append(col_idx + 1)
                valid_years.append(int(y_str))
                
        df_metrics = df_region.iloc[indicator_row_idx+1:].copy()
        df_metrics = df_metrics.dropna(subset=[0])
        
        for idx, row in df_metrics.iterrows():
            indicator_name = str(row[0]).strip()
            if indicator_name == '同比增长' or indicator_name == 'nan' or '来源：' in indicator_name or '注：' in indicator_name:
                continue 
            
            for list_idx, col_idx in enumerate(valid_cols):
                year = valid_years[list_idx]
                val = row[col_idx]
                all_data.append({
                    'province': region_name,
                    'year': year,
                    indicator_name: val
                })
                
    if not all_data:
        return pd.DataFrame()
        
    # 转换为DataFrame，去重处理
    df_long = pd.DataFrame(all_data)
    df_long['value'] = pd.to_numeric(df_long.iloc[:, 2], errors='coerce')
    df_long['indicator'] = df_long.columns[2]
    
    # 因为 all_data 里的 key 是 indicator_name 动态的，上面这句可能有问题，重新构建长表正确逻辑
    clean_data = []
    for item in all_data:
        for k, v in item.items():
            if k not in ['province', 'year']:
                clean_data.append({
                    'province': item['province'],
                    'year': item['year'],
                    'indicator': k,
                    'value': pd.to_numeric(v, errors='coerce')
                })
                
    df_clean = pd.DataFrame(clean_data).dropna(subset=['value'])
    
    if df_clean.empty:
        return pd.DataFrame()

    # 长表转宽表
    df_melted = df_clean.pivot_table(index=['province', 'year'], columns='indicator', values='value').reset_index()
    
    return df_melted

def main():
    print(f"正在处理文件夹: {FOLDER_PATH}")
    
    panel_list = []
    
    for f in os.listdir(FOLDER_PATH):
        file_path = os.path.join(FOLDER_PATH, f)
        if not (f.endswith('.xlsx') or f.endswith('.xls') or f.endswith('.csv')):
            continue
            
        print(f"--> [进入文件]: {f}")
        try:
            if '全国_' in f or '江苏南京苏州_各方面' in f:
                # 已经是 panel 宽表格式的常规表
                df = pd.read_excel(file_path) if f.endswith('.xlsx') else pd.read_csv(file_path)
                
                # 统一大小写和常用别名
                col_map = {}
                for col in df.columns:
                    if col.lower() in ['年份', '时间']: col_map[col] = 'year'
                    if col.lower() in ['地区', '省份', '城市']: col_map[col] = 'province'
                if col_map: df.rename(columns=col_map, inplace=True)
                
                panel_list.append(df)
                print(f"    成功解析常规格式，获取行数: {len(df)}")
                
            elif '补全' in f or '年度数据' in f or '快递数据' in f or '空气质量' in f:
                # 处理国家统计局横向年份格式
                df_nbs = parse_nbs_format(file_path)
                if not df_nbs.empty:
                    panel_list.append(df_nbs)
                    print(f"    成功解析NBS格式，获取行数: {len(df_nbs)}")
                else:
                    print(f"    未找到有效转换数据。")
        except Exception as e:
            print(f"    处理 {f} 失败: {e}")

    # 合并各个宽表块
    print(f"\n======== 开始自动拼接终极宽表 ========")
    if not panel_list:
        print("未找到有效数据！")
        return
        
    df_final = panel_list[0]
    for i in range(1, len(panel_list)):
        df_append = panel_list[i]
        
        # 处理可能的重复列，例如 '_x', '_y'，这里直接 merge 会产生这个
        # 更优雅的合并：更新和并集
        # 这里用两两 merge outer
        intersect_cols = list(set(df_final.columns) & set(df_append.columns) - {'province', 'year'})
        if intersect_cols:
            df_append = df_append.drop(columns=intersect_cols)
            
        df_final = pd.merge(df_final, df_append, on=['province', 'year'], how='outer')
        
    # 清理一些可能的前后缀
    df_final.columns = [str(c).strip() for c in df_final.columns]
    
    out_path = os.path.join(FOLDER_PATH, 'ultimate_panel_master.csv')
    df_final.sort_values(by=['province', 'year'], inplace=True, ascending=[True, False])
    df_final.to_csv(out_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ 拼接完毕！最终宽表保存在: {out_path}")
    print(f"📊 宽表形状(行x列): {df_final.shape}")
    print("\n包含了以下字段(前20个):")
    print(df_final.columns.tolist()[:20])

if __name__ == "__main__":
    main()
