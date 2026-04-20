import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, r'project_v1_index\data\intermediate\panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\tables')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # Check if variables exist
    vars_of_interest = ['carbon_intensity_ln', 'ED_core', 'pgdp_ln', 'pgdp_ln_sq', 'ind2_share', 'urban_rate', 'coal_share']
    missing_vars = [v for v in vars_of_interest if v not in df.columns]
    if missing_vars:
        print(f"[Error] Required variables missing: {missing_vars}")
        return
        
    df_desc = df[vars_of_interest].describe().T
    print("\n--- Descriptive Statistics ---")
    print(df_desc)
    df_desc.to_csv(os.path.join(OUTPUT_DIR, 'descriptive_stats.csv'))
    
    corr = df[vars_of_interest].corr()
    corr.to_csv(os.path.join(OUTPUT_DIR, 'correlation_matrix.csv'))
    
    # 3. Set Up Panel Data
    df_reg = df.dropna(subset=vars_of_interest)
    df_panel = df_reg.set_index(['province', 'year'])
    
    # Dependent variable
    Y = df_panel['carbon_intensity_ln']
    # Independent variables
    X = df_panel[['ED_core', 'pgdp_ln', 'pgdp_ln_sq', 'ind2_share', 'urban_rate', 'coal_share']]
    X = sm.add_constant(X)
    
    # 4. Run Baseline Two-Way Fixed Effects Model
    print("\n--- Baseline Two-Way Fixed Effects Model ---")
    model = PanelOLS(Y, X, entity_effects=True, time_effects=True)
    
    # Specification 1: Clustered standard errors by province
    res_clustered = model.fit(cov_type='clustered', cluster_entity=True)
    print("\n[Model 1] Clustered SE by Province:")
    print(res_clustered.summary)
    
    # Specification 2: Driscoll-Kraay standard errors
    res_dk = model.fit(cov_type='kernel')
    print("\n[Model 2] Driscoll-Kraay SE:")
    print(res_dk.summary)
    
    with open(os.path.join(OUTPUT_DIR, 'baseline_regression_clustered.txt'), 'w', encoding='utf-8') as f:
        f.write(res_clustered.summary.as_text())
        
    with open(os.path.join(OUTPUT_DIR, 'baseline_regression_dk.txt'), 'w', encoding='utf-8') as f:
        f.write(res_dk.summary.as_text())
        
    # Compare Output
    compare_df = pd.DataFrame({
        'Coef': res_clustered.params,
        'Clustered_SE': res_clustered.std_errors,
        'Clustered_Pval': res_clustered.pvalues,
        'DK_SE': res_dk.std_errors,
        'DK_Pval': res_dk.pvalues
    })
    compare_df.to_csv(os.path.join(OUTPUT_DIR, 'baseline_regression.csv'))
        
    print(f"\n[Success] Regression results saved to {OUTPUT_DIR}/baseline_regression.csv")

if __name__ == '__main__':
    main()