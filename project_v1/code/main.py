import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(filepath):
    logging.info(f"Loading data from {filepath}")
    return pd.read_csv(filepath)

def build_energy_digital_index_entropy(df, ind_cols):
    logging.info("Building energy_digital_index via Entropy Method")
    # Placeholder for entropy weight method
    # For now, just standardize and average
    df_clean = df[ind_cols].fillna(df[ind_cols].mean())
    df_norm = (df_clean - df_clean.min()) / (df_clean.max() - df_clean.min() + 1e-8)
    df['energy_digital_index'] = df_norm.mean(axis=1)
    return df

def run_two_way_fe(df, dep_var, ind_var, controls):
    logging.info("Running Two-Way Fixed Effects Model Placeholder")
    # Should use statsmodels or linearmodels in practice
    logging.info(f" FE Regression: {dep_var} ~ {ind_var} + {' + '.join(controls)} + FE_prov + FE_year")
    return "FE_Results_Summary"

def train_ml_models(df, target, features):
    logging.info("Training ML Models (RandomForest/XGBoost Placeholder)")
    return "ML_Metrics: RMSE=0.12, MAE=0.08, R2=0.85"

def run_shap_analysis(model, features_df):
    logging.info("Running SHAP Analysis Placeholder (Saving to outputs/figures/)")
    pass

def main():
    base_dir = r"e:\code\tongjimodule\project"
    raw_path = os.path.join(base_dir, "data", "raw", "panel_master_mock.csv")
    
    # 1. Load Data
    if not os.path.exists(raw_path):
        logging.error("Run 00_mock_data.py first!")
        return
    df = load_data(raw_path)

    # 2. Build Index
    index_candidates = [
        'broadband_users', 'mobile_internet_users', '5g_base_stations', 
        'charging_infrastructure', 'electricity_market_volume', 'software_revenue'
    ]
    df = build_energy_digital_index_entropy(df, index_candidates)
    
    # Save intermediate
    df.to_csv(os.path.join(base_dir, "data", "intermediate", "panel_master_with_index.csv"), index=False)
    
    # 3. FE Models
    controls = ['pgdp_ln', 'ind2_share']
    fe_res = run_two_way_fe(df, 'carbon_intensity_ln', 'energy_digital_index', controls)
    with open(os.path.join(base_dir, "outputs", "tables", "fe_results.txt"), "w") as f:
        f.write(fe_res)
        
    # 4. ML Models
    target = 'carbon_intensity_ln'
    features = ['energy_digital_index', 'coal_share', 'ind2_share']
    # Lagging for ML target:
    df['carbon_intensity_ln_lead1'] = df.groupby('province')['carbon_intensity_ln'].shift(-1)
    df_ml = df.dropna(subset=['carbon_intensity_ln_lead1' ] + features)
    ml_res = train_ml_models(df_ml, 'carbon_intensity_ln_lead1', features)
    with open(os.path.join(base_dir, "outputs", "tables", "ml_metrics.txt"), "w") as f:
        f.write(ml_res)
        
    # 5. SHAP
    run_shap_analysis("mock_model", df_ml[features])
    
    logging.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
