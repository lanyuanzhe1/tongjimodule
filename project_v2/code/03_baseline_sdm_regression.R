# 03_baseline_sdm_regression.R
# R script for Panel Spatial Durbin Model (SDM) Estimation
# 建议工作目录 (Working Directory) 设置在工程根目录: e:/code/tongjimodule

# 1. 加载必要的包 (若未安装需先 install.packages)
options(warn=-1)
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(plm)
  library(splm)
  library(spdep)
  library(lmtest)
})

# ========= 1. 读入数据 =========
cat("\n[1] 读取面板数据与空间权重矩阵...\n")
df <- read_csv("project_v1/data/intermediate/panel_master_with_index.csv", show_col_types = FALSE) %>%
  arrange(province, year)

W_cont <- read.csv("project_v2/data/intermediate/W_contiguity_std.csv",
                   row.names = 1, check.names = FALSE, fileEncoding = "UTF-8-BOM")
W_dist <- read.csv("project_v2/data/intermediate/W_geo_distance_std.csv",
                   row.names = 1, check.names = FALSE, fileEncoding = "UTF-8-BOM")

W_cont <- as.matrix(W_cont)
W_dist <- as.matrix(W_dist)

# --- 新增: 清理名字 ---
# 强制移除可能是BOM或者多余空格的前后空白字符
rownames(W_cont) <- trimws(gsub("^\\xef\\xbb\\xbf", "", rownames(W_cont), useBytes = TRUE))
colnames(W_cont) <- trimws(gsub("^\\xef\\xbb\\xbf", "", colnames(W_cont), useBytes = TRUE))
rownames(W_dist) <- trimws(gsub("^\\xef\\xbb\\xbf", "", rownames(W_dist), useBytes = TRUE))
colnames(W_dist) <- trimws(gsub("^\\xef\\xbb\\xbf", "", colnames(W_dist), useBytes = TRUE))

# ！！！最暴力的修复方案！！！ 
# 既然我们通过 Python 端输出的数据完全可以保证两边代表的同样是同样的 30 个对应省份
# 直接将面板数据提取出来的字母序名字硬塞给 W 矩阵作为行列名即可
prov_order <- sort(unique(df$province))

rownames(W_cont) <- prov_order
colnames(W_cont) <- prov_order
rownames(W_dist) <- prov_order
colnames(W_dist) <- prov_order

stopifnot(identical(rownames(W_cont), prov_order))
stopifnot(identical(colnames(W_cont), prov_order))

# 转成 listw (style = "W" 代表已经是行标准化)
lw_cont <- mat2listw(W_cont, style = "W")
lw_dist <- mat2listw(W_dist, style = "W")

# 转换为面板数据格式
pdf <- pdata.frame(df, index = c("province", "year"))

# ========= 2. 设定公式 (修改：只保留一个数字化指数并改变滞后设定) =========
# 采用对数化处理可能更好地挖掘线性关系
pdf$energy_digital_index_100_ln <- log(pdf$energy_digital_index_100 + 1)

fm_twfe <- carbon_intensity_ln ~ energy_digital_index_100_ln + 
  pgdp_ln + ind2_share + urban_rate + coal_share

fm_sdm <- carbon_intensity_ln ~ energy_digital_index_100_ln + 
  pgdp_ln + ind2_share + urban_rate + coal_share + factor(year)

# ========= 3. 非空间基准：TWFE =========
cat("\n[2] 跑基准模型: 传统的双向固定效应 (TWFE)...\n")
mod_twfe <- plm(
  formula = fm_twfe,
  data = pdf,
  model = "within",
  effect = "twoways"
)
print(summary(mod_twfe))
capture.output(summary(mod_twfe), file = "project_v2/outputs/tables/01_twfe_results.txt")
# ========= 4. 空间桥梁模型：SAR-TWFE (ML估计) =========
cat("\n[3] 跑桥梁模型: 空间自回归模型 (SAR-TWFE, ML估计)...\n")
mod_sar_twfe <- spml(
  formula = fm_twfe,
  data = pdf,
  listw = lw_cont,
  model = "within",
  effect = "twoways",
  lag = TRUE,
  spatial.error = "none"
)
print(summary(mod_sar_twfe))
capture.output(summary(mod_sar_twfe), file = "project_v2/outputs/tables/02_sar_twfe_results.txt")

# ========= 5. 主模型：Panel SDM (GM估计) =========
cat("\n[4] 跑核心主模型: 空间杜宾模型面板 (Panel SDM, GM估计) - 邻接矩阵...\n")
mod_sdm_fe <- spgm(
  formula = fm_sdm,
  data = pdf,
  listw = lw_cont,
  model = "within",  # 配合 factor(year) 实现双向固定
  lag = TRUE,
  Durbin = TRUE,     # 将核心变量和控制变量同时进行空间滞后 (WX)
  spatial.error = FALSE,
  method = "w2sls"
)
print(summary(mod_sdm_fe))
capture.output(summary(mod_sdm_fe), file = "project_v2/outputs/tables/03_sdm_cont_results.txt")

# ========= 6. 效应分解 =========
cat("\n[5] 核心突破: 空间效应偏微分分解 (Direct, Indirect, Total)...\n")
nT <- length(unique(df$year))
# 注意: spgm 与 impacts 联动时，需指定时间维度 nT 以正确解析面板结构
imp_sdm <- impacts(
  mod_sdm_fe,
  listw = lw_cont,
  time = nT,
  R = 500  # 蒙特卡洛模拟次数，用于计算p值
)
sum_imp <- summary(imp_sdm, zstats = TRUE, short = TRUE)
print(sum_imp)
capture.output(sum_imp, file = "project_v2/outputs/tables/04_sdm_cont_impacts.txt")

# ========= 7. 距离矩阵稳健性 =========
cat("\n[6] 稳健性检验: 使用地理距离矩阵的 Panel SDM...\n")
mod_sdm_fe_dist <- spgm(
  formula = fm_sdm,
  data = pdf,
  listw = lw_dist,
  model = "within", 
  lag = TRUE,
  Durbin = TRUE,
  spatial.error = FALSE,
  method = "w2sls"
)
print(summary(mod_sdm_fe_dist))
capture.output(summary(mod_sdm_fe_dist), file = "project_v2/outputs/tables/05_sdm_dist_results.txt")

cat("\n[7] 距离矩阵的效应分解...\n")
imp_sdm_dist <- impacts(
  mod_sdm_fe_dist,
  listw = lw_dist,
  time = nT,
  R = 500
)
sum_imp_dist <- summary(imp_sdm_dist, zstats = TRUE, short = TRUE)
print(sum_imp_dist)
capture.output(sum_imp_dist, file = "project_v2/outputs/tables/06_sdm_dist_impacts.txt")

cat("\n✅ 所有测算均已完成！结果已成功导出至 project_v2/outputs/tables/ 目录下。\n")