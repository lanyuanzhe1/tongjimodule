import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, 'project/data/intermediate/panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, 'project/outputs/tables')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # 1. Descriptive Statistics
    print("\n--- Descriptive Statistics ---")
    vars_of_interest = ['carbon_intensity_ln', 'energy_digital_index_100', 'pgdp_ln', 'ind2_share', 'urban_rate']
    
    # Check if variables exist, drop rows with NaN in these columns for regression
    for v in vars_of_interest:
        if v not in df.columns:
            print(f"[Error] Required variable {v} missing from dataset!")
            return
            
    df_desc = df[vars_of_interest].describe().T
    print(df_desc)
    df_desc.to_csv(os.path.join(OUTPUT_DIR, 'descriptive_stats.csv'))
    
    # 2. Correlation Matrix
    print("\n--- Correlation Matrix ---")
    corr = df[vars_of_interest].corr()
    print(corr)
    corr.to_csv(os.path.join(OUTPUT_DIR, 'correlation_matrix.csv'))
    
    # 3. Set Up Panel Data
    # PanelOLS requires index to be [entity, time]
    df_reg = df.dropna(subset=vars_of_interest)
    df_panel = df_reg.set_index(['province', 'year'])
    
    # Dependent variable
    Y = df_panel['carbon_intensity_ln']
    # Independent variables
    X = df_panel[['energy_digital_index_100', 'pgdp_ln', 'ind2_share', 'urban_rate']]
    X = sm.add_constant(X)
    
    # 4. Run Baseline Two-Way Fixed Effects Model
    print("\n--- Baseline Two-Way Fixed Effects Model ---")
    model = PanelOLS(Y, X, entity_effects=True, time_effects=True)
    
    # Specification 1: Clustered standard errors by province
    res_clustered = model.fit(cov_type='clustered', cluster_entity=True)
    print("\n[Model 1] Clustered SE by Province:")
    print(res_clustered.summary)
    
    # Specification 2: Driscoll-Kraay standard errors (robust to cross-sectional dependence)
    # linearmodels implements this via kernel covariance
    res_dk = model.fit(cov_type='kernel')
    print("\n[Model 2] Driscoll-Kraay SE:")
    print(res_dk.summary)
    
    # Save the summaries
    with open(os.path.join(OUTPUT_DIR, 'baseline_regression_clustered.txt'), 'w', encoding='utf-8') as f:
        f.write(res_clustered.summary.as_text())
        
    with open(os.path.join(OUTPUT_DIR, 'baseline_regression_dk.txt'), 'w', encoding='utf-8') as f:
        f.write(res_dk.summary.as_text())
        
    # Create a comparative CSV table (simplified)
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