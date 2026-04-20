# 综合数字化指数重构方案 (Project V1 Index Reconstruction Strategy)

**日期**：2026年4月20日  
**目标**：解决原数据方案中细分能源数字化特征（如绿电、5G基站等）在部分省份大面积缺失导致的数据孤岛和方差坍缩问题，全面转向基座更稳、覆盖30个省份的广义宏观数字化面板数据。

---

## 一、 核心重构思路
放弃原先的狭义/广义拆分策略，构建唯一且全面的“省级综合数字化发展指数 (`ED_index`)”，并以此作为因果推断主回归的核心解释变量。

### 1. 核心解释变量：省级综合数字化发展指数 (`ED_index`)
**用途**：作为 TWFE、SDM 等面板计量经济学因果推断主回归的**核心解释变量**。
**选表原则**：选取覆盖面广、代表性强、能真实反映地方数字生态繁荣度的宏观及产业应用渗透数据。
**指标构成 (三大维度，8项指标)**：
- **维度 A：数字基础设施** (硬件与传输网络)
  1. `optical_cable_length` (光缆线路长度)
  2. `mobile_internet_traffic` (移动互联网接入流量)
  3. `mobile_internet_users` (移动互联网用户数)
  4. `broadband_users` (互联网宽带接入用户数)
- **维度 B：数字产业化** (IT支撑能力)
  5. `software_revenue` (软件业务收入)
- **维度 C：产业数字化与应用渗透** (企业数字下沉)
  6. `ecommerce_enterprise_ratio` (有电子商务交易活动的企业比重)
  7. `ecommerce_sales` (电子商务销售额)
  8. `ecommerce_purchases` (电子商务采购额)

### 2. 政策牵引力变量补充
- **单独设置/另设用途**：政府工作报告能源数字化关键词词频单独构建为 `policy_attention_energy_digital` (政策关注度)，作为稳健性替换变量、控制变量或工具变量 (IV) 储备。

---

## 二、 指数构建与清洗规则

为了保障量化质量化繁为简，构建流采取以下标准化步骤：

1. **缺失值门槛**：候选指标要求省-年面板覆盖率 $\ge 70\%$。头尾缺失不强行插值，中间年份使用线性插值。
2. **极端值处理**：所有底层子指标进行 $1\% \sim 99\%$ Winsorize 缩尾处理。
3. **量纲统一**：使用 Min-Max 归一化 (投射到 $0-100$ 区间) 或 Z-score 标准化。
4. **权重合成基准**：优先采用**“等权重加总 (Equal Weight)”**作为主版本，摒弃直接过度依赖熵权带来的剧烈波动。
5. **稳健性替换**：使用熵权法 (Entropy Weight) 和主成分分析法 (PCA - 第一主成分) 作为指数构建的稳健性替换版本。

---

## 三、 重构后的模型结构归位

*   **主回归模型 (Baseline Panel FE/SDM)**:
    $$CarbonIntensity_{it} = \beta_1 ED\_index_{it} + \gamma Controls_{it} + \mu_i + \lambda_t + \epsilon_{it}$$
*   **控制变量 (Controls)**:
    `pgdp_ln`, `pgdp_ln_sq`, `urban_rate`, `ind2_share`, `total_energy_consumption_ln`
*   **机制路线 (Mechanisms)**:
    - 产业结构高级化：`tertiary_secondary_ratio` (第三产业与第二产业增加值比重)
    - 能源利用效率跃升：`energy_intensity_ln` (能源消耗强度)
    - 能源供给清洁化：`clean_energy_prod_share` (清洁能源产量占比)