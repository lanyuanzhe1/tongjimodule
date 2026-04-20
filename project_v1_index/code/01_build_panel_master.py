import os
import pandas as pd
import numpy as np
import glob
from itertools import product
from sklearn.decomposition import PCA

DIR_BASE = r'e:\code\tongjimodule'
DIR_0411 = os.path.join(DIR_BASE, 'data/0411')
DIR_0412 = os.path.join(DIR_BASE, 'data/0412')
DIR_CEADS = os.path.join(DIR_BASE, 'data/碳核算数据库/data_ceads_used')
DIR_0419 = os.path.join(DIR_BASE, 'data/0419/能源数字化各省份关键词词频')

OUTPUT_MASTER = os.path.join(DIR_BASE, 'project_v1_index/data/intermediate/panel_master_with_index.csv')
OUTPUT_WEIGHTS = os.path.join(DIR_BASE, 'project_v1_index/outputs/tables/index_weight_table.csv')

def clean_province_name(name):
    if pd.isna(name): return name
    name = str(name).strip()
    name = name.replace('省', '').replace('市', '').replace('回族自治区', '').replace('维吾尔自治区', '').replace('壮族自治区', '').replace('自治区', '')
    if name == '新疆维吾尔': return '新疆'
    if name == '宁夏回族': return '宁夏'
    if name == '广西壮族': return '广西'
    if name == '内蒙古': return '内蒙古'
    return name

py_map = {
    'Beijing': '北京', 'Tianjin': '天津', 'Hebei': '河北', 'Shanxi': '山西', 'Inner mongolia': '内蒙古',
    'Inner Mongolia': '内蒙古', 'Liaoning': '辽宁', 'Jilin': '吉林', 'Heilongjiang': '黑龙江', 
    'Shanghai': '上海', 'Jiangsu': '江苏', 'Zhejiang': '安徽', 'Anhui': '安徽', 'Fujian': '福建', 
    'Jiangxi': '江西', 'Shandong': '山东', 'Henan': '河南', 'Hubei': '湖北', 'Hunan': '湖南', 
    'Guangdong': '广东', 'Guangxi': '广西', 'Hainan': '海南', 'Chongqing': '重庆', 'Sichuan': '四川', 
    'Guizhou': '贵州', 'Yunnan': '云南', 'Shaanxi': '陕西', 'Gansu': '甘肃', 'Qinghai': '青海', 
    'Ningxia': '宁夏', 'Xinjiang': '新疆'
}
py_map['Zhejiang'] = '浙江'

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
    
    rename_cols = {
        '5g基站数（万座）': '5g_base_stations', 
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
        'co2排放量（百万吨）': 'co2_approx',
        '快递业务收入（亿元）': 'express_delivery_revenue'
    }
    
    keep_cols = ['province', 'year']
    for old, new in rename_cols.items():
        if old in df.columns:
            df.rename(columns={old: new}, inplace=True)
            keep_cols.append(new)
            
    if '5g_base_stations' in df.columns and '5g_base_stations_sub' in df.columns:
        df['5g_base_stations'] = df['5g_base_stations'].fillna(df['5g_base_stations_sub'])
        if '5g_base_stations_sub' in keep_cols:
            keep_cols.remove('5g_base_stations_sub')
        df.drop('5g_base_stations_sub', axis=1, inplace=True)
        
    df = df[list(set(keep_cols).intersection(set(df.columns)))]
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
            coal_row = df[df.iloc[:, 1].astype(str).str.contains('Raw coal total', case=False, na=False)]
            coal_data = coal_row.iloc[-1].to_dict() if not coal_row.empty else {}
            
            for i, row in df.iterrows():
                row_vals = row.astype(str).tolist()
                if any([('Total' in v or '总计' in v) for v in row_vals]) and i > 2:
                    data_dict = row.to_dict()
                    for k, v in data_dict.items():
                        if type(k) == str and k not in ['Unnamed: 0', 'Items'] and type(v) in [int, float, np.float64]:
                            coal_v = coal_data.get(k, np.nan)
                            if pd.isna(coal_v):
                                coal_v = 0.0
                            rows.append({'province_pingyin': k, 'year': year, 'co2_total': v, 'coal_emissions': coal_v})
                    break
        except Exception as e:
            print(f"Error parsing CEADS sheet {sheet}: {e}")
            
    df_ceads = pd.DataFrame(rows)
    if 'province_pingyin' not in df_ceads.columns:
        return pd.DataFrame(columns=['province', 'year', 'co2_total'])
        
    df_ceads['province'] = df_ceads['province_pingyin'].str.strip().map(py_map)
    df_ceads.dropna(subset=['province'], inplace=True)
    df_ceads['co2_total'] = pd.to_numeric(df_ceads['co2_total'], errors='coerce')
    df_ceads['coal_emissions'] = pd.to_numeric(df_ceads['coal_emissions'], errors='coerce')
    df_ceads['coal_share'] = df_ceads['coal_emissions'] / df_ceads['co2_total'].replace(0, np.nan)
    return df_ceads[['province', 'year', 'co2_total', 'coal_emissions', 'coal_share']]

def load_0419_policy_attention():
    files = glob.glob(os.path.join(DIR_0419, '*.xlsx'))
    rows = []
    for f in files:
        prov = os.path.basename(f).replace('.xlsx', '')
        prov = clean_province_name(prov)
        df_p = pd.read_excel(f)
        if '年份' in df_p.columns and '总频次' in df_p.columns:
            for _, r in df_p.iterrows():
                y_val = str(r['年份']).strip()
                if y_val == '总计' or y_val == 'nan' or not y_val: continue
                try:
                    rows.append({
                        'province': prov,
                        'year': float(y_val),
                        'policy_attention_energy_digital': float(r['总频次'])
                    })
                except Exception:
                    pass
    return pd.DataFrame(rows)

def build_index_series(df, cols, prefix):
    """ Builds index using Equal Weight, Entropy Weight, and PCA """
    df_idx = df[cols].copy()
    
    # Missing value imputation using median for robustness
    # Fallback to 0 if entire column is missing
    for c in cols:
        val = df_idx[c].median()
        if pd.isna(val):
            val = 0.0
        df_idx[c] = df_idx[c].fillna(val)
    
    # 1% - 99% Winsorize per base variable
    for c in cols:
        p1 = df_idx[c].quantile(0.01)
        p99 = df_idx[c].quantile(0.99)
        if pd.isna(p1): p1 = 0
        if pd.isna(p99): p99 = 0
        df_idx[c] = df_idx[c].clip(lower=p1, upper=p99)
        
        # Max-min scale
        s_min = df_idx[c].min()
        s_max = df_idx[c].max()
        if pd.isna(s_max) or pd.isna(s_min) or s_max == s_min:
            df_idx[c] = 0.0
        else:
            df_idx[c] = (df_idx[c] - s_min) / (s_max - s_min) * 100.0
        df_idx[c] = df_idx[c] / 100.0  # Scale 0-1
    
    # 1. Equal Weight
    res_eq = df_idx.mean(axis=1) * 100.0
    
    # 2. Entropy Weight
    p = df_idx.div(df_idx.sum(axis=0).replace(0, np.nan), axis=1).replace(0, 1e-12).fillna(1e-12)
    # clip just in case
    p = p.clip(lower=1e-12, upper=1.0)
    entropy = -(p * np.log(p)).sum(axis=0) / np.log(max(len(p), 2))
    divergence = 1.0 - entropy
    div_sum = divergence.sum()
    if div_sum == 0: div_sum = 1e-12
    entropy_weights = divergence / div_sum
    res_ent = (df_idx * entropy_weights).sum(axis=1) * 100.0
    
    # 3. PCA
    from sklearn.preprocessing import StandardScaler
    
    if df_idx.var().sum() == 0:
        res_pca = pd.Series(0.0, index=df_idx.index)    
    else:
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_idx)
        
        pca = PCA(n_components=1)
        pca_idx = pca.fit_transform(scaled_data).flatten()
        if pca.components_[0][0] < 0:
            pca_idx = -pca_idx
            
        s_min = pca_idx.min()
        s_max = pca_idx.max()
        if s_min == s_max:
            res_pca = pd.Series(0.0, index=df_idx.index)
        else:
            res_pca = pd.Series((pca_idx - s_min) / (s_max - s_min) * 100.0, index=df_idx.index)
    
    return res_eq, res_ent, res_pca, entropy_weights

def main():
    print("[1/5] Loading all datasets...")
    df_internet = load_internet()
    df_pop = load_pop()
    df_gdp = load_gdp()
    df_0411 = load_0411_master()
    df_ceads = load_ceads()
    df_0419 = load_0419_policy_attention()
    
    provinces = list(set(py_map.values()))
    years = range(2011, 2024)  # Expanded window where possible
    master = pd.DataFrame(list(product(provinces, years)), columns=['province', 'year'])
    master['year'] = master['year'].astype(float)
    
    print("[2/5] Merging panels...")
    for df_sub in [df_gdp, df_pop, df_internet, df_ceads, df_0411, df_0419]:
        if not df_sub.empty:
            df_sub['year'] = df_sub['year'].astype(float)
            master = master.merge(df_sub, on=['province', 'year'], how='left')
    
    # Filter valid analysis window
    master = master[(master['year'] >= 2011) & (master['year'] <= 2022)].copy()

    print("[3/5] Calculating derived control and mechanism variables...")
    master['pgdp'] = (master['gdp_100m'] * 1e8) / master['population_10k'].replace(0, np.nan) / 1e4
    master['pgdp_ln'] = np.log(master['pgdp'].replace(0, np.nan))
    master['pgdp_ln_sq'] = master['pgdp_ln'] ** 2
    master['urban_rate'] = master['urban_pop_10k'] / master['population_10k'].replace(0, np.nan)
    master['ind2_share'] = master['ind2_100m'] / master['gdp_100m'].replace(0, np.nan)
    
    master['carbon_intensity'] = master['co2_total'] / master['gdp_100m'].replace(0, np.nan)
    master['carbon_intensity_ln'] = np.log(master['carbon_intensity'].replace(0, np.nan))
    
    master['co2_total_ln'] = np.log(master['co2_total'].replace(0, np.nan))
    master['carbon_per_capita'] = (master['co2_total'] * 1e6) / (master['population_10k'].replace(0, np.nan) * 10000)
    master['carbon_per_capita_ln'] = np.log(master['carbon_per_capita'].replace(0, np.nan))
    master['tertiary_secondary_ratio'] = master['ind3_100m'] / master['ind2_100m'].replace(0, np.nan)
    
    print("[4/5] Preparing Index Build (Linear Interpolation for inner missing data)...")
    num_cols = master.select_dtypes(include=[np.number]).columns.drop('year')
    for col in num_cols:
        master[col] = master.groupby('province')[col].transform(lambda x: x.interpolate(method='linear', limit_direction='both'))
    
    core_vars = ['electricity_market_volume', 'green_power_trade_volume', 'green_certificate_volume', 
                 'charging_infrastructure', '5g_base_stations', 'iot_terminal_users']
    eco_vars = core_vars + ['software_revenue', 'digital_core_industry_share', 'high_tech_industry_share', 
                            'broadband_users', 'mobile_internet_users', 'optical_cable_length']
    
    core_vars_avail = [x for x in core_vars if x in master.columns]
    eco_vars_avail = [x for x in eco_vars if x in master.columns]
    
    weights_info = []

    print("[5/5] Synthesizing ED_core and ED_eco scales...")
    if len(core_vars_avail) > 0:
        master['ED_core'], master['ED_core_entropy'], master['ED_core_pca'], w_core = build_index_series(master, core_vars_avail, "ED_core")
        for i, c in enumerate(core_vars_avail):
            weights_info.append({'index_name': 'ED_core', 'variable': c, 'entropy_weight': w_core.iloc[i]})
            
    if len(eco_vars_avail) > 0:
        master['ED_eco'], master['ED_eco_entropy'], master['ED_eco_pca'], w_eco = build_index_series(master, eco_vars_avail, "ED_eco")
        for i, c in enumerate(eco_vars_avail):
            weights_info.append({'index_name': 'ED_eco', 'variable': c, 'entropy_weight': w_eco.iloc[i]})

    os.makedirs(os.path.dirname(OUTPUT_MASTER), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_WEIGHTS), exist_ok=True)
    
    master.to_csv(OUTPUT_MASTER, index=False, encoding='utf-8-sig')
    pd.DataFrame(weights_info).to_csv(OUTPUT_WEIGHTS, index=False, encoding='utf-8-sig')
    
    print(f"\n[Done] Pipeline executed successfully.")
    print(f"-> Saved variables panel: {OUTPUT_MASTER}")
    print(f"-> Saved index weights table: {OUTPUT_WEIGHTS}")

if __name__ == '__main__':
    main()
