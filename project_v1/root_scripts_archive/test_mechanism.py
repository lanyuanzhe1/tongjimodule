
import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.panel import PanelOLS

df = pd.read_csv('project/data/intermediate/panel_master_with_index.csv')
df['software_revenue'] = pd.to_numeric(df['software_revenue'], errors='coerce')
df_reg = df.dropna(subset=['carbon_intensity_ln', 'energy_digital_index_100', 'pgdp_ln', 'ind2_share', 'urban_rate', 'software_revenue']).set_index(['province', 'year'])

Y_med1 = df_reg['software_revenue']
Y_main = df_reg['carbon_intensity_ln']
X_base = df_reg[['energy_digital_index_100', 'pgdp_ln', 'ind2_share', 'urban_rate']]
X_med = df_reg[['energy_digital_index_100', 'software_revenue', 'pgdp_ln', 'ind2_share', 'urban_rate']]

try:
    res_m1 = PanelOLS(Y_med1, sm.add_constant(X_base), entity_effects=True, time_effects=True).fit(cov_type='clustered', cluster_entity=True)
    res_m2 = PanelOLS(Y_main, sm.add_constant(X_med), entity_effects=True, time_effects=True).fit(cov_type='clustered', cluster_entity=True)
    print('=== Software M Eq ===')
    print(res_m1.summary)
    print('=== Carbon Y Eq ===')
    print(res_m2.summary)
except Exception as e:
    print(e)

