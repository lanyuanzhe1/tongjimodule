import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, r'project\data\intermediate\panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, r'project\outputs\tables')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define regional mappings
EAST = ['北京市', '天津市', '河北省', '辽宁省', '上海市', '江苏省', '浙江省', '福建省', '山东省', '广东省', '海南省',
        '北京', '天津', '河北', '辽宁', '上海', '江苏', '浙江', '福建', '山东', '广东', '海南']
CENTRAL = ['山西省', '吉林省', '黑龙江省', '安徽省', '江西省', '河南省', '湖北省', '湖南省',
           '山西', '吉林', '黑龙江', '安徽', '江西', '河南', '湖北', '湖南']
WEST = ['内蒙古自治区', '广西壮族自治区', '重庆市', '四川省', '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区',
        '内蒙古', '广西', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']
MUNICIPALITIES = ['北京市', '天津市', '上海市', '重庆市', '北京', '天津', '上海', '重庆']

def run_panel_fe(df, Y_col, X_cols, cov_type='clustered', cluster_entity=True):
    df_reg = df.dropna(subset=[Y_col] + X_cols)
    if df_reg.empty:
        return None
        
    df_panel = df_reg.set_index(['province', 'year'])
    Y = df_panel[Y_col]
    X = df_panel[X_cols]
    X = sm.add_constant(X)
    
    model = PanelOLS(Y, X, entity_effects=True, time_effects=True)
    
    if cov_type == 'clustered':
        res = model.fit(cov_type='clustered', cluster_entity=cluster_entity)
    elif cov_type == 'driscoll_kraay':
        res = model.fit(cov_type='kernel')
    else:
        res = model.fit(cov_type='robust')
        
    return res

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # Define baseline vars
    controls = ['pgdp_ln', 'ind2_share', 'urban_rate']
    base_x = 'energy_digital_index_100'
    base_y = 'carbon_intensity_ln'
    
    print("\n=============================================")
    print("====== 1. Robustness Checks ============")
    print("=============================================")
    robustness_results = []

    # 1.1 Exclude Municipalities
    print("\n[Robustness 1] Exclude Municipalities")
    df_no_muni = df[~df['province'].isin(MUNICIPALITIES)].copy()
    res_no_muni = run_panel_fe(df_no_muni, base_y, [base_x] + controls)
    if res_no_muni:
        robustness_results.append({
            'Model': 'Exclude Municipalities',
            'Coef': res_no_muni.params[base_x],
            'P-val': res_no_muni.pvalues[base_x],
            'R2': res_no_muni.rsquared_within,
            'N': res_no_muni.nobs
        })

    # 1.2 Driscoll-Kraay Standard Errors (Robust to cross-sectional dependence)
    print("\n[Robustness 2] Driscoll-Kraay SE")
    res_dk = run_panel_fe(df, base_y, [base_x] + controls, cov_type='driscoll_kraay')
    if res_dk:
        robustness_results.append({
            'Model': 'Driscoll-Kraay SE',
            'Coef': res_dk.params[base_x],
            'P-val': res_dk.pvalues[base_x],
            'R2': res_dk.rsquared_within,
            'N': res_dk.nobs
        })
        
    # 1.3 Replace Dependent Variable: Carbon Per Capita
    print("\n[Robustness 3] Replace Y with ln(Carbon Per Capita)")
    res_y1 = run_panel_fe(df, 'carbon_per_capita_ln', [base_x] + controls)
    if res_y1:
        robustness_results.append({
            'Model': 'Y = ln(Carbon Per Capita)',
            'Coef': res_y1.params[base_x],
            'P-val': res_y1.pvalues[base_x],
            'R2': res_y1.rsquared_within,
            'N': res_y1.nobs
        })

    # 1.4 Replace Dependent Variable: Total CO2
    print("\n[Robustness 4] Replace Y with ln(Total CO2)")
    res_y2 = run_panel_fe(df, 'co2_total_ln', [base_x] + controls)
    if res_y2:
        robustness_results.append({
            'Model': 'Y = ln(Total CO2)',
            'Coef': res_y2.params[base_x],
            'P-val': res_y2.pvalues[base_x],
            'R2': res_y2.rsquared_within,
            'N': res_y2.nobs
        })
        
    # 1.5 Replace Core Explanatory Variable: PCA Index
    print("\n[Robustness 5] Replace X with PCA Index")
    pca_x = 'energy_digital_index_pca_100'
    res_x = run_panel_fe(df, base_y, [pca_x] + controls)
    if res_x:
        robustness_results.append({
            'Model': 'X = PCA Index',
            'Coef': res_x.params[pca_x],
            'P-val': res_x.pvalues[pca_x],
            'R2': res_x.rsquared_within,
            'N': res_x.nobs
        })
        
    df_robustness = pd.DataFrame(robustness_results)
    print("\n--- Robustness Summary ---")
    print(df_robustness)
    df_robustness.to_csv(os.path.join(OUTPUT_DIR, 'robustness_summary.csv'), index=False)
    
    
    print("\n=============================================")
    print("====== 2. Heterogeneity Analysis =======")
    print("=============================================")
    hetero_results = []
    
    # 2.1 Regional Heterogeneity (East, Central, West)
    print("\n[Heterogeneity 1] Region Splitting")
    df_east = df[df['province'].isin(EAST)].copy()
    df_central = df[df['province'].isin(CENTRAL)].copy()
    df_west = df[df['province'].isin(WEST)].copy()
    
    for region_name, df_reg in zip(['East', 'Central', 'West'], [df_east, df_central, df_west]):
        res_h = run_panel_fe(df_reg, base_y, [base_x] + controls)
        if res_h:
            hetero_results.append({
                'Group': f'Region: {region_name}',
                'Coef': res_h.params[base_x],
                'P-val': res_h.pvalues[base_x],
                'R2': res_h.rsquared_within,
                'N': res_h.nobs
            })
            with open(os.path.join(OUTPUT_DIR, f'heterogeneity_region_{region_name}.txt'), 'w', encoding='utf-8') as f:
                f.write(res_h.summary.as_text())
                
    # 2.2 Digitalization Base Heterogeneity (High vs Low)
    print("\n[Heterogeneity 2] Digitalization Base (High vs Low)")
    prov_mean_digi = df.groupby('province')[base_x].mean()
    median_digi = prov_mean_digi.median()
    high_digi_provs = prov_mean_digi[prov_mean_digi >= median_digi].index
    
    df_high_digi = df[df['province'].isin(high_digi_provs)].copy()
    df_low_digi = df[~df['province'].isin(high_digi_provs)].copy()
    
    res_high_digi = run_panel_fe(df_high_digi, base_y, [base_x] + controls)
    if res_high_digi:
        hetero_results.append({
            'Group': 'Digital Base: High',
            'Coef': res_high_digi.params[base_x],
            'P-val': res_high_digi.pvalues[base_x],
            'R2': res_high_digi.rsquared_within,
            'N': res_high_digi.nobs
        })
        
    res_low_digi = run_panel_fe(df_low_digi, base_y, [base_x] + controls)
    if res_low_digi:
        hetero_results.append({
            'Group': 'Digital Base: Low',
            'Coef': res_low_digi.params[base_x],
            'P-val': res_low_digi.pvalues[base_x],
            'R2': res_low_digi.rsquared_within,
            'N': res_low_digi.nobs
        })
        
    # 2.3 Coal Dependence Heterogeneity (High vs Low)
    print("\n[Heterogeneity 3] Coal Dependence (High vs Low)")
    # Fallback to ind2_share if coal_share is missing
    coal_col = 'coal_share' if 'coal_share' in df.columns else 'ind2_share'
    prov_mean_coal = df.groupby('province')[coal_col].mean()
    median_coal = prov_mean_coal.median()
    high_coal_provs = prov_mean_coal[prov_mean_coal >= median_coal].index
    
    df_high_coal = df[df['province'].isin(high_coal_provs)].copy()
    df_low_coal = df[~df['province'].isin(high_coal_provs)].copy()
    
    res_high_coal = run_panel_fe(df_high_coal, base_y, [base_x] + controls)
    if res_high_coal:
        hetero_results.append({
            'Group': 'Coal Dep: High',
            'Coef': res_high_coal.params[base_x],
            'P-val': res_high_coal.pvalues[base_x],
            'R2': res_high_coal.rsquared_within,
            'N': res_high_coal.nobs
        })
        
    res_low_coal = run_panel_fe(df_low_coal, base_y, [base_x] + controls)
    if res_low_coal:
        hetero_results.append({
            'Group': 'Coal Dep: Low',
            'Coef': res_low_coal.params[base_x],
            'P-val': res_low_coal.pvalues[base_x],
            'R2': res_low_coal.rsquared_within,
            'N': res_low_coal.nobs
        })

    df_hetero = pd.DataFrame(hetero_results)
    print("\n--- Heterogeneity Summary ---")
    print(df_hetero)
    df_hetero.to_csv(os.path.join(OUTPUT_DIR, 'heterogeneity_summary.csv'), index=False)
    
    print(f"\n[Success] Robustness and Heterogeneity tests completed. Results saved to {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
