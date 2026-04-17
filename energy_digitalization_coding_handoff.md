# 能源数字化—区域碳减排项目技术交接文档（供 Coding AI 执行）

## 1. 项目概述

### 1.1 目标
构建一套完整的技术系统，用于研究：

**《能源数字化对区域碳减排的影响机制与预测研究——基于双向固定效应与可解释机器学习》**

系统需要同时完成以下四件事：

1. 将“能源数字化”量化为可复用的综合指数；
2. 用面板统计模型识别其对区域碳减排的影响；
3. 拆解其作用机制；
4. 用机器学习对未来碳排放强度进行预测，并用 SHAP 做可解释性分析。

---

## 2. 研究主线

### 2.1 技术闭环
本项目不是简单堆砌“指数 + FE + XGBoost”，而是要形成如下闭环：

- **结构化量化**：构建能源数字化指数
- **因果识别**：双向固定效应 / 稳健性 / 滞后项 / 可选 IV
- **机制拆解**：能源结构、绿色创新、产业升级/能效改善
- **预测校验**：RF / XGBoost / LightGBM / Elastic Net
- **可解释回扣**：SHAP 解释全局、局部和交互效应

### 2.2 分层设计
建议分为两层：

#### A. 主分析层（核心）
- 样本：全国 30 省级地区 × 2011–2023 年
- 用途：主识别、机制、稳健性、预测

#### B. 案例层（辅助）
- 区域：江苏 / 南京 / 苏州
- 用途：案例展示、情景解释、可视化补充
- 注意：不要让案例层承担主识别任务

---

## 3. 数据架构设计

### 3.1 主键
统一主键：

- `province`
- `year`

案例层可扩展：
- `city`
- `year`

### 3.2 推荐目录结构
```text
project/
├─ data/
│  ├─ raw/
│  ├─ clean/
│  ├─ intermediate/
│  └─ final/
├─ code/
│  ├─ 01_ingest.py
│  ├─ 02_clean_merge.py
│  ├─ 03_build_index.py
│  ├─ 04_descriptive.py
│  ├─ 05_fe_models.py
│  ├─ 06_mechanism.py
│  ├─ 07_robustness.py
│  ├─ 08_ml_forecast.py
│  ├─ 09_shap_analysis.py
│  └─ utils.py
├─ outputs/
│  ├─ tables/
│  ├─ figures/
│  ├─ logs/
│  └─ models/
└─ docs/
   ├─ variable_dict.xlsx
   ├─ source_log.md
   └─ technical_notes.md
```

### 3.3 数据表层次
#### `raw_*`
- 原始下载/整理文件
- 不做实质性改动

#### `clean_*`
- 统一地区名、年份、单位
- 处理缺失和异常

#### `panel_master`
- 最终用于建模的省级面板主表

#### `case_city_panel`
- 江苏 / 南京 / 苏州的案例数据表

---

## 4. 变量体系设计

## 4.1 因变量（Y）
### 主因变量
- `carbon_intensity_ln`
- 定义：`ln(CO2 / GDP)`

### 替代因变量
- `carbon_per_capita_ln` = `ln(CO2 / population)`
- `co2_total_ln` = `ln(CO2_total)`

优先使用碳排放强度作为主因变量，因为目标是刻画绿色转型效率，而不是简单比较总量。

---

## 4.2 核心解释变量（X）
### `energy_digital_index`
能源数字化综合指数。

建议拆成三个一级维度：

#### 维度 A：数字基础设施
候选变量：
- 宽带接入用户数
- 移动互联网用户数
- 5G 基站数
- 光缆线路长度
- 物联网终端用户数

#### 维度 B：能源数字应用
候选变量：
- 充电基础设施总量
- 电力市场交易电量
- 绿电交易电量
- 绿证交易量
- 可再生能源装机占比
- 智能电网 / 配电自动化代理变量（若能获取）

#### 维度 C：数字产业支撑
候选变量：
- 软件业务收入
- 电信业务收入
- 信息技术服务收入
- 数字经济核心产业增加值占比
- 高技术产业占比
- R&D 强度

---

## 4.3 控制变量（C）
建议控制但避免与核心指数重复：

- `pgdp_ln`：人均 GDP 对数
- `pgdp_ln_sq`：人均 GDP 对数平方
- `ind2_share`：第二产业占比
- `urban_rate`：城镇化率
- `coal_share`：煤炭消费占比
- `open_rate`：对外开放度
- `env_gov`：环境治理强度
- `pop_density_ln`：人口密度对数

### 重要规则
如果某个变量已经进入 `energy_digital_index`，原则上不要再单独放回控制变量中。

---

## 4.4 机制变量（M）
固定三条主机制：

### 机制 1：能源结构优化
候选：
- `coal_share`
- `renewable_share`
- `clean_power_share`

### 机制 2：绿色技术创新
候选：
- `green_patent_ln`
- `rd_intensity`
- `tech_market_turnover_ln`

### 机制 3：产业升级 / 能效改善
候选：
- `tertiary_secondary_ratio`
- `energy_intensity_ln`
- `industrial_energy_efficiency`

---

## 5. 指数构建方案

### 5.1 主方案
**熵权法** 构建 `energy_digital_index`

### 5.2 替代方案
为稳健性保留两个替代构造：

1. PCA 主成分法
2. 标准化后等权加总

### 5.3 指数构建规则
1. 指标先做方向统一
2. 极端值先缩尾（建议 1% 或 2.5%）
3. 再做标准化
4. 缺失值按统一规则处理后再进指数
5. 输出每个维度和总指数
6. 输出权重表

### 5.4 输出文件
- `energy_digital_index_entropy.csv`
- `energy_digital_index_pca.csv`
- `energy_digital_index_equal.csv`
- `index_weight_table.csv`

---

## 6. 基准统计模型

### 6.1 双向固定效应模型
主模型：

```math
Y_it = β ED_it + γ X_it + μ_i + λ_t + ε_it
```

其中：
- `Y_it`：碳排放强度
- `ED_it`：能源数字化指数
- `X_it`：控制变量
- `μ_i`：地区固定效应
- `λ_t`：年份固定效应

### 6.2 标准误
- 主结果：省级聚类稳健标准误
- 稳健性：Driscoll-Kraay 标准误

### 6.3 需要输出的回归版本
至少包括：

1. 只加 FE 的空模型
2. 加核心解释变量
3. 加部分控制变量
4. 加全部控制变量
5. 不同标准误设定版本

### 6.4 诊断项
- 描述统计
- 相关系数矩阵
- VIF
- 异常值/离群值检查
- 截面相关检验（若可行）

---

## 7. 机制模型

### 7.1 面板中介框架
第一步：

```math
M_it = a ED_it + θ X_it + μ_i + λ_t + u_it
```

第二步：

```math
Y_it = c' ED_it + b M_it + θ X_it + μ_i + λ_t + v_it
```

### 7.2 对每条机制分别跑：
- 能源结构机制
- 绿色创新机制
- 产业升级/能效机制

### 7.3 输出
- 机制回归表
- 中介路径图
- bootstrap 中介效应区间（若实现成本可接受）

---

## 8. 稳健性设计

至少完成以下 6 项中的 4 项：

1. 替换因变量
2. 替换核心解释变量构造方式
3. 核心解释变量滞后一期
4. 缩尾后重跑
5. 子样本敏感性（如去直辖市/去资源型地区）
6. Driscoll-Kraay 标准误

### 可选增强
- 工具变量 IV
- 动态面板 / System GMM（仅附加，不作为主模型）

---

## 9. 异质性分析

建议只做三组，避免发散：

1. 东中西分组
2. 高/低数字化基础分组
3. 高/低煤炭依赖分组

输出：
- 分组回归表
- 系数比较图

---

## 10. 机器学习预测系统

## 10.1 预测目标
建议预测下一期碳排放强度：

- `target = carbon_intensity_ln_lead1`

即预测 `t+1` 年的碳排放强度。

---

## 10.2 特征工程
特征分四类：

### A. 结构特征
- 产业结构
- 城镇化率
- 对外开放度
- 能源结构

### B. 数字化特征
- 总指数
- 子指数
- 5G / 宽带 / 软件收入等原始变量

### C. 动态特征
- 滞后一期碳排放强度
- 滞后一期能源数字化指数
- 滞后一期能耗强度

### D. 交互和变化率特征
- `digital × coal_share`
- `digital × ind2_share`
- 指数同比增速
- 碳强度同比变化率

---

## 10.3 模型池
建议至少跑以下 4 个模型：

- Elastic Net（线性参照）
- Random Forest
- XGBoost
- LightGBM

### 可选
- CatBoost（若类别变量处理方便）

---

## 10.4 训练验证方式
不要随机切分。

推荐：
- 时间滚动验证 / expanding window

示例：
- 2011–2018 训练，预测 2019
- 2011–2019 训练，预测 2020
- 2011–2020 训练，预测 2021
- ...

### 评价指标
- RMSE
- MAE
- R²

输出：
- `ml_metrics.csv`
- `prediction_vs_actual.csv`
- 模型性能对比图

---

## 11. SHAP 可解释性

### 11.1 必做图
至少输出：

1. SHAP summary / beeswarm
2. SHAP bar plot
3. 关键变量 dependence plot
4. 关键交互图（可选）

### 11.2 重点变量
优先解释：
- `energy_digital_index`
- `coal_share`
- `green_patent_ln` / `rd_intensity`
- `carbon_intensity_lag1`
- `ind2_share`

### 11.3 解释目标
SHAP 不是单独展示，而是要与 FE 结果对应：

- FE 给出平均方向
- SHAP 给出非线性和异质性贡献
- 二者结合形成“统计识别 + 预测解释”闭环

---

## 12. 案例层任务（江苏 / 南京 / 苏州）

### 12.1 用途
案例层不要承担主识别，而是承担：

- 数据可视化
- 区域时序图
- 区域对比图
- 情景说明
- 指标样例展示

### 12.2 案例层已有候选字段
- GDP
- 用电量
- 宽带接入用户
- 5G 或 5G 在网用户
- 新能源汽车保有量
- PM2.5
- 空气质量优良天数比率
- 快递业务量
- 高新技术产业占比

### 12.3 注意
案例层数据存在较多 NA，不应用于完整主回归，仅用于展示和补充验证。

---

## 13. 数据清洗规范

### 13.1 命名规范
全部英文蛇形命名，如：
- `energy_digital_index`
- `carbon_intensity_ln`
- `green_patent_ln`

### 13.2 地区统一
- 北京市 → 北京
- 内蒙古自治区 → 内蒙古
- 新疆维吾尔自治区 → 新疆
统一形成映射表。

### 13.3 缺失值规则
- 中间年份少量缺失：线性插值
- 首尾大段缺失：不插值，改代理变量或删除该指标
- 指数构建前必须记录缺失比例

### 13.4 极端值处理
- 建议 1% 或 2.5% winsorize
- 原始数据保留，不覆盖

### 13.5 日志
所有清洗和变换操作必须写日志：
- `cleaning_log.md`
- `variable_dict.xlsx`

---

## 14. 推荐输出物清单

### 14.1 数据输出
- `panel_master.csv`
- `case_city_panel.csv`
- `energy_digital_index_entropy.csv`
- `energy_digital_index_pca.csv`
- `energy_digital_index_equal.csv`

### 14.2 表格输出
- 描述统计表
- 相关系数矩阵
- 基准回归表
- 机制分析表
- 异质性分析表
- 稳健性表
- ML 指标对比表

### 14.3 图形输出
- 技术路线图
- 能源数字化指数时序图
- 区域对比图
- 基准回归系数图
- SHAP beeswarm
- SHAP bar
- 预测值 vs 实际值图

---

## 15. 编码执行顺序（建议）

### Stage 1：数据底座
1. ingest raw files
2. unify province/year
3. build clean tables
4. merge into `panel_master`

### Stage 2：变量工程
5. build derived variables
6. build `energy_digital_index`
7. export variable dictionary draft

### Stage 3：统计识别
8. descriptive stats
9. baseline FE
10. mechanism models
11. heterogeneity
12. robustness

### Stage 4：预测系统
13. feature engineering
14. rolling validation
15. train 4 models
16. compare metrics

### Stage 5：解释层
17. SHAP
18. align SHAP with FE results
19. export tables and figures

---

## 16. 验收标准

Coding AI 完成后，至少应满足：

1. 能生成一个可直接使用的省级面板主表；
2. 能生成 3 种版本的能源数字化指数；
3. 能跑通双向固定效应主模型；
4. 能输出至少 1 套机制结果；
5. 能跑通至少 3 个预测模型；
6. 能产出 SHAP 全局解释图；
7. 所有结果可复现，路径清晰，无手工改表依赖。

---

## 17. 暂不处理但可预留的增强模块
以下可先预留接口，不必第一轮就完成：

- 政策文本量化指数
- 空间溢出 / 空间杜宾模型
- 工具变量自动筛选
- 情景模拟（未来数字化提升下的减排路径）
- 贝叶斯不确定性量化

---

## 18. 给 Coding AI 的直接执行要求

1. 优先保证**数据结构正确、流程可复现、结果能导出**；
2. 不要一开始追求花哨模型；
3. 所有步骤模块化；
4. 关键参数可配置；
5. 所有表图自动保存；
6. 所有衍生变量通过代码生成；
7. 对于缺失严重变量，先保留接口，不强行伪造。

---

## 19. 当前已知信息与设计约束（重要）

- 当前已有一批全国层面的数字化与能源相关年度指标，以及江苏、南京、苏州的案例层数据；
- 江苏、南京、苏州数据中存在较多 `NA` 和口径不齐问题，因此更适合作为案例层；
- 项目方向应保持“绿色发展 / 双碳 + 统计严谨性 + AI 工具合理使用”的组合；
- 题目技术主线应优先围绕面板统计模型、稳健性和机器学习解释闭环构建。

---

## 20. 最终一句话摘要
请基于“全国省级面板主分析 + 江苏南京苏州案例补充”的双层架构，实现一套从数据清洗、指数构建、双向固定效应、机制检验、稳健性分析，到机器学习预测与 SHAP 解释的完整可复现技术系统。
