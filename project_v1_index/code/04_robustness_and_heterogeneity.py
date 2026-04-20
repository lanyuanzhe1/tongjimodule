import os
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, r'project_v1_index\data\intermediate\panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\tables')
os.makedirs(OUTPUT_DIR, exist_ok=True)

MUNICIPALITIES = ['北京', '天津', '上海', '重庆']
EAST = ['北京', '天津', '河北', '辽宁', '上海', '江苏', '浙江', '福建', '山东', '广东', '海南']
CENTRAL = ['山西', '吉林', '黑龙江', '安徽', '江西', '河南', '湖北', '湖南']
WEST = ['内蒙古', '广西', '重庆', '四川', '贵州', '云南', '西藏', '陕西', '甘肃', '青海', '宁夏', '新疆']

def run_panel_fe(df, Y_col, X_cols, cov_type='clustered', cluster_entity=True):
    df_reg = df.dropna(subset=[Y_col] + X_cols)
    if df_reg.empty: return None
    df_panel = df_reg.set_index(['province', 'year'])
    Y = df_panel[Y_col]
    X = sm.add_constant(df_panel[X_cols])
    model = PanelOLS(Y, X, entity_effects=True, time_effects=True)
    if cov_type == 'clustered':
        res = model.fit(cov_type='clustered', cluster_entity=cluster_entity)
    else:
        res = model.fit(cov_type='kernel')
    return res

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    controls = ['pgdp_ln', 'pgdp_ln_sq', 'ind2_share', 'urban_rate', 'coal_share']
    base_x = 'ED_core'
    base_y = 'carbon_intensity_ln'
    
    print("\n====== 1. Robustness Checks ======")
    robustness_results = []

    # 1. Exclude Municipalities
    res_no_muni = run_panel_fe(df[~df['province'].isin(MUNICIPALITIES)].copy(), base_y, [base_x] + controls)
    if res_no_muni:
        robustness_results.append({'Model': 'Exclude Municipalities', 'Coef': res_no_muni.params[base_x], 'P-val': res_no_muni.pvalues[base_x], 'R2': res_no_muni.rsquared_within})

    # 2. Replace Core X with PCA Index Edition
    if 'ED_core_pca' in df.columns:
        res_x_pca = run_panel_fe(df, base_y, ['ED_core_pca'] + controls)
        if res_x_pca:
            robustness_results.append({'Model': 'X = ED_core (PCA)', 'Coef': res_x_pca.params['ED_core_pca'], 'P-val': res_x_pca.pvalues['ED_core_pca'], 'R2': res_x_pca.rsquared_within})
            
    # 3. Target Alternative: Total CO2
    res_y_tot = run_panel_fe(df, 'co2_total_ln', [base_x] + controls)
    if res_y_tot:
        robustness_results.append({'Model': 'Y = ln(Total CO2)', 'Coef': res_y_tot.params[base_x], 'P-val': res_y_tot.pvalues[base_x], 'R2': res_y_tot.rsquared_within})

    # 4. Use Policy Attention as IV or Proxy Control Regression (Just testing as proxy X here)
    if 'policy_attention_energy_digital' in df.columns:
        res_x_policy = run_panel_fe(df, base_y, ['policy_attention_energy_digital'] + controls)
        if res_x_policy:
            var_n = 'policy_attention_energy_digital'
            robustness_results.append({'Model': 'X = Policy Word Frequency', 'Coef': res_x_policy.params[var_n], 'P-val': res_x_policy.pvalues[var_n], 'R2': res_x_policy.rsquared_within})

    df_robustness = pd.DataFrame(robustness_results)
    print("\n--- Robustness Summary ---")
    print(df_robustness)
    df_robustness.to_csv(os.path.join(OUTPUT_DIR, 'robustness_summary.csv'), index=False)
    
    print("\n====== 2. Heterogeneity Analysis ======")
    hetero_results = []
    
    # East vs Central vs West
    for region_name, lst in zip(['East', 'Central', 'West'], [EAST, CENTRAL, WEST]):
        res_reg = run_panel_fe(df[df['province'].isin(lst)].copy(), base_y, [base_x] + controls)
        if res_reg:
            hetero_results.append({'Group': f'Region: {region_name}', 'Coef': res_reg.params[base_x], 'P-val': res_reg.pvalues[base_x]})
            
    df_hetero = pd.DataFrame(hetero_results)
    print("\n--- Heterogeneity Summary ---")
    print(df_hetero)
    df_hetero.to_csv(os.path.join(OUTPUT_DIR, 'heterogeneity_summary.csv'), index=False)

if __name__ == '__main__':
    main()