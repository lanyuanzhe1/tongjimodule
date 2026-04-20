import os
import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, KFold, cross_val_score, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

DIR_BASE = r'e:\code\tongjimodule'
INPUT_FILE = os.path.join(DIR_BASE, r'project_v1_index\data\intermediate\panel_master_with_index.csv')
OUTPUT_FIG_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\figures')
OUTPUT_TAB_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\tables')
OUTPUT_MOD_DIR = os.path.join(DIR_BASE, r'project_v1_index\outputs\models')

os.makedirs(OUTPUT_FIG_DIR, exist_ok=True)
os.makedirs(OUTPUT_TAB_DIR, exist_ok=True)
os.makedirs(OUTPUT_MOD_DIR, exist_ok=True)

def plot_actual_vs_predicted(y_test, y_pred, output_path):
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, y_pred, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
    plt.xlabel("Actual Carbon Intensity (ln)")
    plt.ylabel("Predicted Carbon Intensity (ln)")
    plt.title("XGBoost: Actual vs Predicted")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    print(f"Loading data from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # 1. 变量与特征工程 (Target T+1 Forecasting)
    # ML model uses the broader Ecosystem ED Index to maximize predictive power 
    # and feature interactions (as stated in variables.yaml & strategy doc)
    features = ['ED_eco', 'pgdp_ln', 'ind2_share', 'urban_rate', 'coal_share']
    target = 'carbon_intensity_ln'
    
    df_clean = df.dropna(subset=features + [target]).copy()
    X = df_clean[features]
    y = df_clean[target]
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 2. 超参数调优 (Hyperparameter Tuning via RandomizedSearchCV)
    print("\n--- Phase 1: Hyperparameter Tuning via RandomizedSearchCV ---")
    param_dist = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 4, 5, 6],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0],
        'min_child_weight': [1, 3]
    }
    
    base_xgb = xgb.XGBRegressor(random_state=42, n_jobs=-1)
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=20, 
        scoring='neg_mean_squared_error',
        cv=cv,
        verbose=1,
        random_state=42,
        n_jobs=-1
    )
    
    random_search.fit(X_train, y_train)
    best_model = random_search.best_estimator_
    
    # 3. Evaluation
    cv_scores = cross_val_score(best_model, X_train, y_train, cv=cv, scoring='r2')
    y_pred_train = best_model.predict(X_train)
    y_pred_test = best_model.predict(X_test)
    
    test_r2 = r2_score(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    metrics_str = (
        f"--- XGBoost Performance Metrics ---\n"
        f"Train CV R2 (5-Fold): {cv_scores.mean():.4f}\n"
        f"Train Set R2:         {r2_score(y_train, y_pred_train):.4f}\n"
        f"Test Set R2:          {test_r2:.4f}\n"
        f"Test RMSE:            {test_rmse:.4f}\n"
    )
    print(metrics_str)
    
    with open(os.path.join(OUTPUT_TAB_DIR, 'ml_metrics.txt'), 'w', encoding='utf-8') as f:
        f.write(metrics_str)
        
    plot_actual_vs_predicted(y_test, y_pred_test, os.path.join(OUTPUT_FIG_DIR, 'xgb_actual_vs_predicted.png'))
    model_path = os.path.join(OUTPUT_MOD_DIR, 'xgboost_best_model.pkl')
    joblib.dump(best_model, model_path)
    
    # 4. SHAP Explanations
    print("\n--- Generating SHAP Explanations ---")
    explainer = shap.TreeExplainer(best_model)
    shap_values = explainer.shap_values(X)
    
    # Global Importance
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, show=False)
    plt.title("SHAP Global Feature Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_summary_plot.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # Dependence Plots
    plt.figure(figsize=(8, 6))
    shap.dependence_plot('ED_eco', shap_values, X, show=False, interaction_index='auto')
    plt.title("SHAP Dependence Plot: Marginal Effect of Energy Digital Eco Index")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_dependence_ED_eco.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Waterfall plot
    try:
        explanation = shap.Explanation(values=shap_values[0], base_values=explainer.expected_value, data=X.iloc[0], feature_names=features)
        plt.figure(figsize=(10, 5))
        shap.waterfall_plot(explanation, show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_waterfall_single_sample.png'), dpi=300, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"[Alert] Could not generate waterfall plot: {e}")

    print("\n[Success] ML Prediction and SHAP pipeline completed.")

if __name__ == '__main__':
    main()