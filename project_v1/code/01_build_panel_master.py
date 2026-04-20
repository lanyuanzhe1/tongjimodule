import os
import sys
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Inputs
DIR_BASE = r'e:\code\tongjimodule'
DIR_0411 = os.path.join(DIR_BASE, 'data/0411')
DIR_0412 = os.path.join(DIR_BASE, 'data/0412')
DIR_CEADS = os.path.join(DIR_BASE, 'data/碳核算数据库/data_ceads_used')
OUTPUT_FILE = os.path.join(DIR_BASE, 'project/data/intermediate/panel_master_with_index.csv')

def clean_province_name(name):
    """Normalize province names completely."""
    if pd.isna(name):
        return name
    name = str(name).strip()
    name = name.replace('省', '').replace('市', '').replace('回族自治区', '').replace('维吾尔自治区', '').replace('壮族自治区', '').replace('自治区', '')
    if name == '新疆维吾尔': return '新疆'
    if name == '宁夏回族': return '宁夏'
    if name == '广西壮族': return '广西'
    if name == '内蒙古': return '内蒙古'
    return name

def load_internet():
    df = pd.read_csv(f'{DIR_0412}/分省互联网主要指标_多年期_面板数据.csv', encoding='utf-8')
    df['province'] = df['省份'].apply(clean_province_name)
    df.rename(columns={'年份': 'year'}, inplace=True)
    df['broadband_users'] = pd.to_numeric(df.get('互联网宽带接入用户 (万户)', np.nan), errors='coerce')
    df['mobile_internet_users'] = pd.to_numeric(df.get('移动互联网用户 (万户)', np.nan), errors='coerce')
    return df[['province', 'year', 'broadband_users', 'mobile_internet_users']]

def load_pop():
    df = pd.read_csv(f'{DIR_0412}/分省人口_多年期_面板数据.csv', encoding='utf-8')
    df['province'] = df['省份'].apply(clean_province_name)
    df.rename(columns={'年份': 'year'}, inplace=True)
    df['population_10k'] = pd.to_numeric(df.get('年末常住人口 (万人)', np.nan), errors='coerce')
    df['urban_pop_10k'] = pd.to_numeric(df.get('城镇人口 (万人)', np.nan), errors='coerce')
    df['rural_pop_10k'] = pd.to_numeric(df.get('乡村人口 (万人)', np.nan), errors='coerce')
    return df[['province', 'year', 'population_10k', 'urban_pop_10k', 'rural_pop_10k']]

def load_gdp():
    df = pd.read_csv(f'{DIR_0412}/分省GDP_多年期_面板数据.csv', encoding='utf-8')
    df['province'] = df['省份'].apply(clean_province_name)
    df.rename(columns={'年份': 'year'}, inplace=True)
    df['gdp_100m'] = pd.to_numeric(df.get('地区生产总值 (亿元)', np.nan), errors='coerce')
    df['ind2_100m'] = pd.to_numeric(df.get('第二产业增加值 (亿元)', np.nan), errors='coerce')
    df['ind3_100m'] = pd.to_numeric(df.get('第三产业增加值 (亿元)', np.nan), errors='coerce')
    return df[['province', 'year', 'gdp_100m', 'ind2_100m', 'ind3_100m']]

def load_0411_master():
    df = pd.read_csv(f'{DIR_0411}/master_panel_4x15.csv', encoding='utf-8')
    if 'province' not in df.columns:
        df.rename(columns={'省份': 'province', '年份': 'year'}, inplace=True)
    df['province'] = df['province'].apply(clean_province_name)
    df = df[df['province'] != 'allcountry']
    
    # Selecting columns mapped to our mechanism/index definitions
    rename_cols = {
        '5g基站数（万座）': '5g_base_stations', # fallback or use '5G基站数（万个）' if needed
        '5G基站数（万个）': '5g_base_stations_sub',
        '光缆线路长度(公里)': 'optical_cable_length',
        '物联网终端用户数（万户）': 'iot_terminal_users',
        '公共充电桩': 'charging_infrastructure',
        '电力市场交易电量（亿千瓦时）': 'electricity_market_volume',
        '绿电交易电量（亿千瓦时）': 'green_power_trade_volume',
        '绿证交易量（万张）': 'green_certificate_volume',
        '可再生能源装机占比（%）': 'renewable_installation_share',
        '软件业务收入（亿元）': 'software_revenue',
        '高新技术产业产值占规上工业比重': 'high_tech_industry_share',
        '数字经济核心产业增加值占GDP比重': 'digital_core_industry_share',
        '空气质量优良天数比率': 'aqi_good_rate',
        'co2排放量（百万吨）': 'co2_approx', # Alternative indicator
        '快递业务收入（亿元）': 'express_delivery_revenue'
    }
    
    # Only keep mapped columns plus keys
    keep_cols = ['province', 'year']
    for old, new in rename_cols.items():
        if old in df.columns:
            df.rename(columns={old: new}, inplace=True)
            keep_cols.append(new)
            
    # Coalesce 5g
    if '5g_base_stations' in df.columns and '5g_base_stations_sub' in df.columns:
        df['5g_base_stations'] = df['5g_base_stations'].fillna(df['5g_base_stations_sub'])
        keep_cols.remove('5g_base_stations_sub')
        df.drop('5g_base_stations_sub', axis=1, inplace=True)
        
    df = df[list(set(keep_cols).intersection(set(df.columns)))]
    # Convert all object types except province to numeric
    for col in df.columns:
        if col not in ['province', 'year']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    return df

def load_ceads():
    excel_path = os.path.join(DIR_CEADS, '表观碳排放清单_1997-2022.xlsx')
    xl = pd.ExcelFile(excel_path)
    sheets = [str(s) for s in xl.sheet_names if str(s).isdigit() and int(s) >= 2011]
    
    rows = []
    for sheet in sheets:
        year = int(sheet)
        try:
            df = xl.parse(sheet)
            # Find the coal row (usually raw 0 in exactly the format CEADS uses)
            coal_row = df[df.iloc[:, 1].astype(str).str.contains('Raw coal total', case=False, na=False)]
            coal_data = coal_row.iloc[-1].to_dict() if not coal_row.empty else {}
            
            # Row index 0 usually is headers, row -1 is usually "Total" or similar
            # Iterate to find the row where "Items" or "Total" is mentioned
            for i, row in df.iterrows():
                row_vals = row.astype(str).tolist()
                if any([('Total' in v or '总计' in v) for v in row_vals]) and i > 2:
                    data_dict = row.to_dict()
                    for k, v in data_dict.items():
                        if type(k) == str and k not in ['Unnamed: 0', 'Items'] and type(v) in [int, float, np.float64]:
                            coal_v = coal_data.get(k, np.nan)
                            rows.append({'province_pingyin': k, 'year': year, 'co2_total': v, 'coal_emissions': coal_v})
                    break
        except Exception as e:
            print(f"Error parsing CEADS sheet {sheet}: {e}")
            
    df_ceads = pd.DataFrame(rows)
    if 'province_pingyin' not in df_ceads.columns:
        return pd.DataFrame(columns=['province', 'year', 'co2_total'])
        
    py_map = {
        'Beijing': '北京', 'Tianjin': '天津', 'Hebei': '河北', 'Shanxi': '山西', 'Inner mongolia': '内蒙古',
        'Inner Mongolia': '内蒙古', 'Liaoning': '辽宁', 'Jilin': '吉林', 'Heilongjiang': '黑龙江', 
        'Shanghai': '上海', 'Jiangsu': '江苏', 'Zhejiang': '浙江', 'Anhui': '安徽', 'Fujian': '福建', 
        'Jiangxi': '江西', 'Shandong': '山东', 'Henan': '河南', 'Hubei': '湖北', 'Hunan': '湖南', 
        'Guangdong': '广东', 'Guangxi': '广西', 'Hainan': '海南', 'Chongqing': '重庆', 'Sichuan': '四川', 
        'Guizhou': '贵州', 'Yunnan': '云南', 'Shaanxi': '陕西', 'Gansu': '甘肃', 'Qinghai': '青海', 
        'Ningxia': '宁夏', 'Xinjiang': '新疆'
    }
    df_ceads['province'] = df_ceads['province_pingyin'].str.strip().map(py_map)
    df_ceads.dropna(subset=['province'], inplace=True)
    df_ceads['co2_total'] = pd.to_numeric(df_ceads['co2_total'], errors='coerce')
    df_ceads['coal_emissions'] = pd.to_numeric(df_ceads['coal_emissions'], errors='coerce')
    df_ceads['coal_share'] = df_ceads['coal_emissions'] / df_ceads['co2_total']
    return df_ceads[['province', 'year', 'co2_total', 'coal_emissions', 'coal_share']]

def ew_method(data_series):
    """Simple Entropy Weight Method on a Matrix"""
    df_norm = (data_series - data_series.min()) / (data_series.max() - data_series.min())
    # Add small epsilon to avoid log(0)
    p = df_norm / df_norm.sum()
    p = p.replace(0, 1e-9)
    e = -(p * np.log(p)).sum() / np.log(len(data_series))
    d = 1 - e
    w = d / d.sum()
    idx = (df_norm * w).sum(axis=1)
    return idx, w

def main():
    print("Loading datasets...")
    df_internet = load_internet()
    df_pop = load_pop()
    df_gdp = load_gdp()
    df_0411 = load_0411_master()
    df_ceads = load_ceads()
    
    print("Pre-merging dataframes...")
    provinces = df_ceads['province'].dropna().unique() if not df_ceads.empty else py_map.values()
    years = range(2016, 2023)  # 2016-2022
    
    # We create a foundational grid
    from itertools import product
    master = pd.DataFrame(list(product(provinces, years)), columns=['province', 'year'])
    
    master = master.merge(df_gdp, on=['province', 'year'], how='left')
    master = master.merge(df_pop, on=['province', 'year'], how='left')
    master = master.merge(df_internet, on=['province', 'year'], how='left')
    master = master.merge(df_ceads, on=['province', 'year'], how='left')
    
    df_0411['year'] = df_0411['year'].astype(float)
    master['year'] = master['year'].astype(float)
    master = master.merge(df_0411, on=['province', 'year'], how='left')
    
    print("Calculating Baseline Derived Features...")
    try:
        master['pgdp'] = (master['gdp_100m'] * 1e8) / (master['population_10k'] * 1e4)
        master['pgdp_ln'] = np.log(master['pgdp'].replace(0, np.nan))
        master['urban_rate'] = master['urban_pop_10k'] / master['population_10k']
        master['ind2_share'] = master['ind2_100m'] / master['gdp_100m']
        
        # 1. 主因变量：碳排放强度
        master['carbon_intensity'] = master['co2_total'] / master['gdp_100m']
        master['carbon_intensity_ln'] = np.log(master['carbon_intensity'].replace(0, np.nan))
        
        # 2. 替代因变量（用于稳健性检验）
        master['co2_total_ln'] = np.log(master['co2_total'].replace(0, np.nan))
        # 假设 co2_total 单位如果是百万吨(1e6)，population_10k 是万人(1e4)
        master['carbon_per_capita'] = (master['co2_total'] * 1e6) / (master['population_10k'] * 10000)
        master['carbon_per_capita_ln'] = np.log(master['carbon_per_capita'].replace(0, np.nan))
        
    except Exception as e:
        print(f"Warning deriving math features: {e}")
        
    print("Interpolating Missing Data (Linear)...")
    num_cols = master.select_dtypes(include=[np.number]).columns.drop('year')
    for col in num_cols:
        master[col] = master.groupby('province')[col].transform(lambda x: x.interpolate(method='linear', limit_direction='both'))
        
    print("Calculating Energy Digital Index (Entropy Method)...")
    index_features = [
        'broadband_users', 
        'mobile_internet_users', 
        '5g_base_stations', 
        'optical_cable_length', 
        'iot_terminal_users', 
        'software_revenue', 
        #'high_tech_industry_share'
    ]
    
    # Filter to only the columns that actually loaded 
    av_features = [f for f in index_features if f in master.columns]
    
    if len(av_features) > 0:
        # Impute index features with 0 if remaining completely missing after interpolation
        master[av_features] = master[av_features].fillna(0)
        
        # --- 熵权法(主构建方案) ---
        idx, w = ew_method(master[av_features])
        master['energy_digital_index'] = idx
        master['energy_digital_index_100'] = idx * 100
        print("Entropy weights generated:", w.to_dict())
        
        # --- 主成分分析PCA(稳健性替代方案) ---
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(master[av_features])
        pca = PCA(n_components=1)
        # 用第一主成分作为总指数
        pca_idx = pca.fit_transform(df_scaled).flatten()
        
        # 根据变量与第一主成分的载荷修正符号（确保该指数正向表示数字化）
        # 如果多数特征（如宽带用户）的载荷为负，则翻转符号
        if pca.components_[0][0] < 0:
            pca_idx = -pca_idx
            
        # 归一化到 0-1 与熵权法尺度齐平
        pca_idx_norm = (pca_idx - pca_idx.min()) / (pca_idx.max() - pca_idx.min())
        master['energy_digital_index_pca'] = pca_idx_norm
        master['energy_digital_index_pca_100'] = pca_idx_norm * 100
        print(f"PCA index generated. First component explained variance: {pca.explained_variance_ratio_[0]:.4f}")
        
    else:
        print("Warning: Missing subset indices for entropy method.")
        
    # Winsorize at 1% and 99%
    lower_bound = master[num_cols].quantile(0.01)
    upper_bound = master[num_cols].quantile(0.99)
    master[num_cols] = master[num_cols].clip(lower=lower_bound, upper=upper_bound, axis=1)
    
    # Output Master Table
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    master.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n[Success] Master panel perfectly built with shape: {master.shape}.")
    print(f"Saved correctly at -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()