import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def calculate_global_moran_i(x, w_matrix, permutations=999):
    """
    手动计算基于行标准化空间权重矩阵的全局莫兰指数(Global Moran's I)
    参数:
    x (pd.Series/np.array): 截面数据向量
    w_matrix (np.ndarray): n x n 行标准化空间权重矩阵
    permutations (int): 蒙特卡洛模拟随机排列的次数，用于计算p值
    """
    n = len(x)
    x_mean = np.mean(x)
    z = x - x_mean
    
    # 因为 W 是行标准化的，所有元素之和 S0 = n
    S0 = n
    
    # 真实 Moran's I
    numerator = z.T @ w_matrix @ z
    denominator = np.sum(z**2)
    moran_i = (n / S0) * (numerator / denominator)
    
    # 蒙特卡洛模拟显著性检验
    simulated_i = np.zeros(permutations)
    for i in range(permutations):
        z_shuffled = np.random.permutation(z)
        sim_num = z_shuffled.T @ w_matrix @ z_shuffled
        simulated_i[i] = (n / S0) * (sim_num / denominator)
        
    e_i = np.mean(simulated_i)
    v_i = np.var(simulated_i)
    
    z_score = (moran_i - e_i) / np.sqrt(v_i)
    # 双侧检验 p 值
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return moran_i, z_score, p_value

def plot_local_moran(x, w_matrix, labels, var_name, year, save_path):
    """
    绘制局部莫兰散点图 (Local Moran's I Scatter Plot)
    四个象限分别代表：第I象限(高-高，HH)，第II象限(低-高，LH)，第III象限(低-低，LL)，第IV象限(高-低，HL)
    """
    # 标准化变量
    x_std = (x - np.mean(x)) / np.std(x)
    # 空间滞后项
    w_x_std = w_matrix @ x_std
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(x=x_std, y=w_x_std, s=50, color='b')
    
    # 添加辅助线切分四个象限
    plt.axhline(0, color='k', linestyle='--', alpha=0.5)
    plt.axvline(0, color='k', linestyle='--', alpha=0.5)
    
    # 拟合全局莫兰线
    m, b = np.polyfit(x_std, w_x_std, 1)
    plt.plot(x_std, m*x_std + b, color='r', linestyle='-', label=f"Global Moran's I (Slope) = {m:.3f}")
    
    # 添加省份标签
    for i, label in enumerate(labels):
        plt.text(x_std[i] + 0.05, w_x_std[i], label, fontsize=9)
        
    plt.title(f"{year}年 {var_name} 局部莫兰散点图 (Local Moran's I)", fontsize=14)
    plt.xlabel(f"{var_name} (标准化 Z-Score)", fontsize=12)
    plt.ylabel(f"空间滞后项 W_{var_name} (标准化 Z-Score)", fontsize=12)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    print("🚀 [Step 1] Loading Panel Data & Spatial Weights...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, '../project_v1/data/intermediate/panel_master_with_index.csv')
    w_cont_path = os.path.join(base_dir, 'data/intermediate/W_contiguity_std.csv')
    w_dist_path = os.path.join(base_dir, 'data/intermediate/W_geo_distance_std.csv')
    
    df = pd.read_csv(data_path, encoding='utf-8-sig')
    years = sorted(df['year'].unique().tolist())
    
    # 读取权重矩阵并保证顺序与 groupby 中的 province 顺序一致
    w_cont_df = pd.read_csv(w_cont_path, index_col=0, encoding='utf-8-sig')
    w_dist_df = pd.read_csv(w_dist_path, index_col=0, encoding='utf-8-sig')
    
    provinces = sorted(df['province'].unique().tolist())
    # 检查省份对齐情况
    assert list(w_cont_df.index) == provinces, "Weight matrix structure mismatch with panel data provinces!"
    
    w_cont_mat = w_cont_df.values
    w_dist_mat = w_dist_df.values
    
    targets = {
        'carbon_intensity_ln': '碳排放强度(对数)',
        'energy_digital_index_100': '能源数字经济指数'
    }
    
    results = []
    
    print("\n🚀 [Step 2] Calculating Global Moran's I for each year & matrix...")
    for target_var, var_label in targets.items():
        for year in years:
            sub_df = df[df['year'] == year].sort_values('province')
            x = sub_df[target_var].values
            
            # 使用邻接矩阵计算
            mi_cont, z_cont, p_cont = calculate_global_moran_i(x, w_cont_mat)
            # 使用距离矩阵计算
            mi_dist, z_dist, p_dist = calculate_global_moran_i(x, w_dist_mat)
            
            results.append({
                'Variable': target_var,
                'Year': int(year),
                "Moran's I (Contiguity)": round(mi_cont, 4),
                "Z-Score (Contiguity)": round(z_cont, 4),
                "P-Value (Contiguity)": round(p_cont, 4),
                "Moran's I (Distance)": round(mi_dist, 4),
                "Z-Score (Distance)": round(z_dist, 4),
                "P-Value (Distance)": round(p_dist, 4)
            })
            
            # 选择最后一年 (如2022年) 绘制局部莫兰散点图
            if year == years[-1]:
                # 默认使用邻接矩阵绘图以展示近邻聚集效应
                plot_save_path = os.path.join(base_dir, f'outputs/figures/Local_Moran_{target_var}_{int(year)}.png')
                plot_local_moran(x, w_cont_mat, np.array(provinces), var_label, int(year), plot_save_path)
                print(f"📊 已生成 {var_label} ({int(year)}年) 散点图: {plot_save_path}")
                
    result_df = pd.DataFrame(results)
    output_tb_path = os.path.join(base_dir, 'outputs/tables/global_moran_i_results.csv')
    result_df.to_csv(output_tb_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 莫兰检验全部完成！统计表已保存至: {output_tb_path}")
    print("\n汇总预览:")
    print(result_df[result_df['Variable'] == 'carbon_intensity_ln'][['Year', "Moran's I (Contiguity)", "P-Value (Contiguity)"]].to_string(index=False))

if __name__ == '__main__':
    # 设定 NumPy 随机种子保证检验的可重复性
    np.random.seed(42)
    main()