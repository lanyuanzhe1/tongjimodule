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
INPUT_FILE = os.path.join(DIR_BASE, r'project\data\intermediate\panel_master_with_index.csv')
OUTPUT_FIG_DIR = os.path.join(DIR_BASE, r'project\outputs\figures')
OUTPUT_TAB_DIR = os.path.join(DIR_BASE, r'project\outputs\tables')
OUTPUT_MOD_DIR = os.path.join(DIR_BASE, r'project\outputs\models')

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
    
    # 1. 变量与特征工程 (Features Selection)
    features = ['energy_digital_index_100', 'pgdp_ln', 'ind2_share', 'urban_rate', 'coal_share']
    target = 'carbon_intensity_ln'
    
    df_clean = df.dropna(subset=features + [target]).copy()
    X = df_clean[features]
    y = df_clean[target]
    
    # 划分训练集和测试集（评估模型泛化能力）
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Dataset split: Train shape {X_train.shape}, Test shape {X_test.shape}")

    # 2. 超参数调优 (Hyperparameter Tuning via RandomizedSearchCV)
    print("\n--- Phase 1: Hyperparameter Tuning via RandomizedSearchCV ---")
    param_dist = {
        'n_estimators': [100, 200, 300, 500],
        'max_depth': [3, 4, 5, 6, 8],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'subsample': [0.6, 0.8, 1.0],
        'colsample_bytree': [0.6, 0.8, 1.0],
        'min_child_weight': [1, 3, 5],
        'gamma': [0, 0.1, 0.2]
    }
    
    base_xgb = xgb.XGBRegressor(random_state=42, n_jobs=-1)
    
    # 使用 5 折交叉验证确保非偶然拟合
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    
    random_search = RandomizedSearchCV(
        estimator=base_xgb,
        param_distributions=param_dist,
        n_iter=30,  # 迭代30次寻找最优组合
        scoring='neg_mean_squared_error',
        cv=cv,
        verbose=1,
        random_state=42,
        n_jobs=-1
    )
    
    random_search.fit(X_train, y_train)
    best_model = random_search.best_estimator_
    print(f"\n[Search Result] Best Parameters Strategy:")
    print(random_search.best_params_)
    
    # 3. 交叉验证与全盘评估 (Cross-Validation Evaluation & Metrics)
    print("\n--- Phase 2: Comprehensive Evaluation ---")
    cv_scores = cross_val_score(best_model, X_train, y_train, cv=cv, scoring='r2')
    
    y_pred_train = best_model.predict(X_train)
    y_pred_test = best_model.predict(X_test)
    
    test_r2 = r2_score(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    
    metrics_str = (
        f"--- XGBoost Performance Metrics ---\n"
        f"Train CV R2 (5-Fold): {cv_scores.mean():.4f} (std: {cv_scores.std():.4f})\n"
        f"Train Set R2:         {train_r2:.4f}\n"
        f"Test Set R2:          {test_r2:.4f}\n"
        f"Test RMSE:            {test_rmse:.4f}\n"
        f"Test MAE:             {test_mae:.4f}\n"
    )
    print(metrics_str)
    
    with open(os.path.join(OUTPUT_TAB_DIR, 'ml_metrics.txt'), 'w', encoding='utf-8') as f:
        f.write(metrics_str)
        
    # 保存拟合优度散点图
    plot_actual_vs_predicted(y_test, y_pred_test, os.path.join(OUTPUT_FIG_DIR, 'xgb_actual_vs_predicted.png'))
    
    # 保存最佳模型以供持续调用
    model_path = os.path.join(OUTPUT_MOD_DIR, 'xgboost_best_model.pkl')
    joblib.dump(best_model, model_path)
    print(f"[Export] Saved best pipeline model to {model_path}")
    
    # --- Phase 3: Generating SHAP Explanations ---
    print("\n--- Phase 3: Generating SHAP Explanations ---")
    
    # [Fix] With XGBoost 1.7.6, JSON parsing works out of the box with TreeExplainer
    explainer = shap.TreeExplainer(best_model)
    shap_values = explainer.shap_values(X)
    
    # 4.1. SHAP 全局特征重要性摘要图 (Summary Plot)
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X, show=False)
    plt.title("SHAP Global Feature Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_summary_plot.png'), dpi=300, bbox_inches='tight')
    plt.close()

    # 4.2. SHAP 核心阈值非线性依赖图 (Dependence Plots)
    # 为 `energy_digital_index_100` 画交叉影响依赖图，精确捕捉“门槛效应点”
    plt.figure(figsize=(8, 6))
    shap.dependence_plot('energy_digital_index_100', shap_values, X, show=False, interaction_index='auto')
    plt.title("SHAP Dependence Plot: Marginal Effect of Energy Digital Index")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_dependence_energy_digital.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 附赠一张：展示煤炭依赖度的边际碳排突增图
    plt.figure(figsize=(8, 6))
    shap.dependence_plot('coal_share', shap_values, X, show=False)
    plt.title("SHAP Dependence Plot: Marginal Effect of Coal Share")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_dependence_coal_share.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4.3 局域样本解释力（以单个省份的单个年份解释原因：Waterfall plot）
    try:
        # 获取第一条有效数据的实例解析（可以是任何你关心的省市代码映射行）
        explanation = shap.Explanation(values=shap_values[0], base_values=explainer.expected_value, data=X.iloc[0], feature_names=features)
        plt.figure(figsize=(10, 5))
        shap.waterfall_plot(explanation, show=False)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_FIG_DIR, 'shap_waterfall_single_sample.png'), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"[Export] Generated Waterfall Plot for a local instance insight.")
    except Exception as e:
        print(f"[Alert] Could not generate waterfall plot: {e}")

    print("\n[Success] Professional pipeline for XGBoost and SHAP analysis is successfully executed.")

if __name__ == '__main__':
    main()
