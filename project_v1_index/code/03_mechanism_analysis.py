import os
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, r'project_v1_index\data\intermediate\panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\tables')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_mechanism(df, M, X_core, controls, Y, out_name):
    vars_needed = [Y, M, X_core] + controls
    df_reg = df.dropna(subset=vars_needed).copy()
    if df_reg.empty:
        print(f"Skipping Mechanism {M}: No valid data.")
        return
        
    df_panel = df_reg.set_index(['province', 'year'])
    
    # Step 1: X -> M
    Y_m1 = df_panel[M]
    X_m1 = sm.add_constant(df_panel[[X_core] + controls])
    model_step1 = PanelOLS(Y_m1, X_m1, entity_effects=True, time_effects=True)
    res_step1_dk = model_step1.fit(cov_type='kernel')
    
    # Step 2: X + M -> Y
    Y_m2 = df_panel[Y]
    X_m2 = sm.add_constant(df_panel[[X_core, M] + controls])
    model_step2 = PanelOLS(Y_m2, X_m2, entity_effects=True, time_effects=True)
    res_step2_dk = model_step2.fit(cov_type='kernel')
    
    print(f'\n=== Mechanism: {M} (Driscoll-Kraay) ===')
    print('>>> Step 1 (X -> M)')
    print(res_step1_dk.summary)
    print('\n>>> Step 2 (X + M -> Y)')
    print(res_step2_dk.summary)
    
    with open(os.path.join(OUTPUT_DIR, out_name), 'w', encoding='utf-8') as f:
        f.write(f'=== Mechanism: {M} ===\n\n')
        f.write('>>> Step 1 (X -> M)\n')
        f.write(res_step1_dk.summary.as_text())
        f.write('\n\n>>> Step 2 (X + M -> Y)\n')
        f.write(res_step2_dk.summary.as_text())

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    controls = ['pgdp_ln', 'pgdp_ln_sq', 'ind2_share', 'urban_rate', 'coal_share']
    target = 'carbon_intensity_ln'
    x_core = 'ED_core'
    
    # Run mechanisms
    # 1. Energy Structure Optimization (Renewable Share)
    # The variable may be completely null if poorly matched, check first:
    df['renewable_installation_share'] = pd.to_numeric(df.get('renewable_installation_share', np.nan), errors='coerce')
    run_mechanism(df, M='renewable_installation_share', X_core=x_core, 
                  controls=controls, Y=target, out_name='mechanism_renewable_share.txt')
                  
    # 2. Industrial Upgrade & Efficiency (Tertiary vs Secondary)
    df['tertiary_secondary_ratio'] = pd.to_numeric(df.get('tertiary_secondary_ratio', np.nan), errors='coerce')
    run_mechanism(df, M='tertiary_secondary_ratio', X_core=x_core, 
                  controls=controls, Y=target, out_name='mechanism_ind_upgrade.txt')

    print(f"\n[Success] Mechanism results saved to {OUTPUT_DIR}")

if __name__ == '__main__':
    main()