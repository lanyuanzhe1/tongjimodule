import os
import pandas as pd
import numpy as np

# ====== 1. 省会城市经纬度字典 ======
# 数据来源：民政部/国家基础地理信息中心
# 用于生成带有地理分布信息的 W_distance (反距离空间权重矩阵)
PROVINCE_COORDS = {
    '北京': [116.4074, 39.9042],
    '天津': [117.2009, 39.0841],
    '河北': [114.5025, 38.0455],  # 石家庄
    '山西': [112.5489, 37.8706],  # 太原
    '内蒙古': [111.7656, 40.8175], # 呼和浩特
    '辽宁': [123.4315, 41.8057],  # 沈阳
    '吉林': [125.3235, 43.8171],  # 长春
    '黑龙江': [126.6425, 45.7570], # 哈尔滨
    '上海': [121.4737, 31.2304],
    '江苏': [118.7969, 32.0603],  # 南京
    '浙江': [120.1528, 30.2886],  # 杭州
    '安徽': [117.2272, 31.8206],  # 合肥
    '福建': [119.2965, 26.0745],  # 福州
    '江西': [115.8580, 28.6820],  # 南昌
    '山东': [117.1201, 36.6512],  # 济南
    '河南': [113.6253, 34.7466],  # 郑州
    '湖北': [114.3054, 30.5928],  # 武汉
    '湖南': [112.9388, 28.2282],  # 长沙
    '广东': [113.2644, 23.1291],  # 广州
    '广西': [108.3661, 22.8172],  # 南宁
    '海南': [110.3295, 20.0174],  # 海口
    '重庆': [106.5516, 29.5630],
    '四川': [104.0665, 30.5723],  # 成都
    '贵州': [106.7135, 26.5790],  # 贵阳
    '云南': [102.7123, 25.0406],  # 昆明
    '陕西': [108.9398, 34.3416],  # 西安
    '甘肃': [103.8263, 36.0594],  # 兰州
    '青海': [101.7782, 36.6171],  # 西宁
    '宁夏': [106.2309, 38.4872],  # 银川
    '新疆': [87.6168, 43.7928]    # 乌鲁木齐
}

# ====== 2. 0-1 拓扑邻接关系 ======
# 用于生成 W_contiguity (0-1邻接空间权重矩阵)
# 注：孤岛海南省通常在空间计量经济学中被规定为与广东省邻接，以避免孤立点导致的矩阵奇异
CONTIGUOUS_NEIGHBORS = {
    '北京': ['天津', '河北'],
    '天津': ['北京', '河北'],
    '河北': ['北京', '天津', '山西', '内蒙古', '辽宁', '山东', '河南'],
    '山西': ['河北', '内蒙古', '陕西', '河南'],
    '内蒙古': ['黑龙江', '吉林', '辽宁', '河北', '山西', '陕西', '宁夏', '甘肃'],
    '辽宁': ['吉林', '内蒙古', '河北'],
    '吉林': ['黑龙江', '内蒙古', '辽宁'],
    '黑龙江': ['内蒙古', '吉林'],
    '上海': ['江苏', '浙江'],
    '江苏': ['山东', '安徽', '浙江', '上海'],
    '浙江': ['江苏', '安徽', '江西', '福建', '上海'],
    '安徽': ['山东', '江苏', '浙江', '江西', '湖北', '河南'],
    '福建': ['浙江', '江西', '广东'],
    '江西': ['安徽', '浙江', '福建', '广东', '湖南', '湖北'],
    '山东': ['河北', '河南', '安徽', '江苏'],
    '河南': ['河北', '山东', '安徽', '湖北', '陕西', '山西'],
    '湖北': ['河南', '安徽', '江西', '湖南', '重庆', '陕西'],
    '湖南': ['湖北', '江西', '广东', '广西', '贵州', '重庆'],
    '广东': ['福建', '江西', '湖南', '广西', '海南'],
    '广西': ['广东', '湖南', '贵州', '云南'],
    '海南': ['广东'],  # 人为相连
    '重庆': ['湖北', '湖南', '贵州', '四川', '陕西'],
    '四川': ['重庆', '贵州', '云南', '青海', '甘肃', '陕西'],
    '贵州': ['四川', '重庆', '湖南', '广西', '云南'],
    '云南': ['四川', '贵州', '广西'], # 西藏不在样本内
    '陕西': ['内蒙古', '山西', '河南', '湖北', '重庆', '四川', '甘肃', '宁夏'],
    '甘肃': ['内蒙古', '宁夏', '陕西', '四川', '青海', '新疆'],
    '青海': ['甘肃', '四川', '新疆'], # 西藏不在样本内
    '宁夏': ['内蒙古', '陕西', '甘肃'],
    '新疆': ['甘肃', '青海'] # 西藏不在样本内
}

def calculate_spherical_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点间的球面距离 (Haversine formula)，返回单位：公里"""
    # 极半径公里
    r = 6371.0
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c

def row_standardize(matrix: pd.DataFrame) -> pd.DataFrame:
    """对矩阵进行行标准化处理 (使每行权重之和为1)"""
    row_sums = matrix.sum(axis=1)
    # 处理孤岛 (以防有全为0的行)
    row_sums[row_sums == 0] = 1 
    return matrix.div(row_sums, axis=0)

def generate_spatial_weights(save_dir_raw: str, save_dir_inter: str):
    print("🚀 [Step 1] Loading Base Panel Province List...")
    # 获取在 project_v1 中的省份精准排序
    # 为了防止 V2 和 V1 的数据行错位，我们必须保证矩阵列名和 df['province'] 的唯一序列一致
    try:
        v1_data_path = os.path.join(BASE_DIR, '../project_v1/data/intermediate/panel_master_with_index.csv')
        v1_df = pd.read_csv(v1_data_path, encoding='utf-8-sig')
        provinces = sorted(v1_df['province'].unique().tolist()) # 保持字母序/拼音序
        print(f"找到 {len(provinces)} 个省份样本。")
    except Exception as e:
        print(f"警告：无法读取 v1 文件 {e}。退回使用字典键。")
        provinces = sorted(list(PROVINCE_COORDS.keys()))

    print("\n🚀 [Step 2] Translating Coordinates & Saving Raw Data...")
    coords_df = pd.DataFrame([{
        'province': p,
        'longitude': PROVINCE_COORDS[p][0],
        'latitude': PROVINCE_COORDS[p][1]
    } for p in provinces])
    coords_csv_path = os.path.join(save_dir_raw, 'province_coordinates.csv')
    coords_df.to_csv(coords_csv_path, index=False, encoding='utf-8-sig')
    print(f"坐标文件已写入: {coords_csv_path}")

    print("\n🚀 [Step 3] Building Distance Matrix (1/d)...")
    dist_matrix = pd.DataFrame(0.0, index=provinces, columns=provinces)
    for p1 in provinces:
        for p2 in provinces:
            if p1 != p2:
                lon1, lat1 = PROVINCE_COORDS[p1]
                lon2, lat2 = PROVINCE_COORDS[p2]
                d = calculate_spherical_distance(lon1, lat1, lon2, lat2)
                # 使用距离的倒数作为空间权重 (反比例权重)
                dist_matrix.loc[p1, p2] = 1.0 / d
    
    # 行标准化 
    dist_matrix_std = row_standardize(dist_matrix)
    dist_csv_path = os.path.join(save_dir_inter, 'W_geo_distance_std.csv')
    dist_matrix_std.to_csv(dist_csv_path, encoding='utf-8-sig')
    print(f"地理距离行标准化矩阵已写入: {dist_csv_path}")

    print("\n🚀 [Step 4] Building Contiguity Matrix (0-1)...")
    cont_matrix = pd.DataFrame(0.0, index=provinces, columns=provinces)
    for p1 in provinces:
        neighbors = CONTIGUOUS_NEIGHBORS.get(p1, [])
        for p2 in neighbors:
            if p2 in provinces:
                cont_matrix.loc[p1, p2] = 1.0

    # 行标准化
    cont_matrix_std = row_standardize(cont_matrix)
    cont_csv_path = os.path.join(save_dir_inter, 'W_contiguity_std.csv')
    cont_matrix_std.to_csv(cont_csv_path, encoding='utf-8-sig')
    print(f"0-1邻接行标准化矩阵已写入: {cont_csv_path}")

if __name__ == '__main__':
    # 路径配置
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    INTER_DIR = os.path.join(BASE_DIR, 'data', 'intermediate')
    
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(INTER_DIR, exist_ok=True)
    
    generate_spatial_weights(RAW_DIR, INTER_DIR)
