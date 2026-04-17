
import os
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, 'project/data/intermediate/panel_master_with_index.csv')
OUTPUT_DIR = os.path.join(DIR_BASE, 'project/outputs/tables')

def run_mechanism(df, M, X_core, controls, Y, out_name):
    vars_needed = [Y, M, X_core] + controls
    df_reg = df.dropna(subset=vars_needed).copy()
    df_panel = df_reg.set_index(['province', 'year'])
    
    # Step 1
    Y_m1 = df_panel[M]
    X_m1 = sm.add_constant(df_panel[[X_core] + controls])
    model_step1 = PanelOLS(Y_m1, X_m1, entity_effects=True, time_effects=True)
    res_step1_dk = model_step1.fit(cov_type='kernel')
    
    # Step 2
    Y_m2 = df_panel[Y]
    X_m2 = sm.add_constant(df_panel[[X_core, M] + controls])
    model_step2 = PanelOLS(Y_m2, X_m2, entity_effects=True, time_effects=True)
    res_step2_dk = model_step2.fit(cov_type='kernel')
    
    print(f'\n=== Mechanism: {M} (Driscoll-Kraay) ===')
    print('>>> Step 1 (X -> M)')
    print(res_step1_dk.summary)
    print('\n>>> Step 2 (X + M -> Y)')
    print(res_step2_dk.summary)

def main():
    df = pd.read_csv(INPUT_FILE)
    df['tertiary_secondary_ratio'] = df['ind3_100m'] / df['ind2_100m']
    run_mechanism(df, M='coal_share', X_core='energy_digital_index_100', 
                  controls=['pgdp_ln', 'urban_rate', 'ind2_share'], Y='carbon_intensity_ln',
                  out_name='mechanism_coal_share_dk.txt')

if __name__ == '__main__':
    main()

