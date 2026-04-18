建立空间计量经济学中的**空间杜宾模型（Spatial Durbin Model, SDM）**作为 project_v2 的基准（Baseline），是一个非常契合理局、且极具学术价值的决定。碳排放和数字经济都有极强的网络和外溢属性。

在正式编写新代码之前，我为你制定了这份**《Project v2：基于空间杜宾模型（SDM）的实证分析实施方案》**。请结合我们在 project_v1 中积累的数据基础进行审阅。

---

### 📊 Project v2: 空间杜宾模型（SDM）实施计划书

#### 阶段一：前置数据准备与空间权重矩阵构建 (Spatial Weight Matrix)

空间计量的核心在于捕捉“邻里效应”，因此首先必须量化省份之间的“空间距离”。

* **任务 1.1：复用 v1 面板数据**：直接从 panel_master_with_index.csv 读取极度完善的基准特征库。
* **任务 1.2：构建空间权重矩阵 $W$**（非常关键，我们需要提供多种矩阵以备稳健性检验）：
  1. **邻接矩阵 (Queen Contiguity Matrix)**：0-1矩阵，地理上接壤为1，否则为0。
  2. **地理距离矩阵 (Geographical Distance Matrix)**：基于省会城市经纬度的球面距离的倒数（$\frac{1}{d_{ij}}$）。
  3. **经济距离矩阵 (Economic Distance Matrix)**：基于两省人均GDP绝对差值的倒数（考察经济层面的依附和溢出）。
  4. **嵌套矩阵 (Nested Matrix)**：地理×经济/人口距离矩阵的结合。
* **产出**：`01_build_spatial_weights.py`

#### 阶段二：空间自相关检验 (Spatial Autocorrelation Test)

在跑模型前，必须先“证明”数据确实存在空间集聚，否则空间计量模型将失去正当性。

* **任务 2.1：全局莫兰指数 (Global Moran's I)**：每年计算因变量（碳排放强度）和核心自变量（数字化指数）的 Moran's I 及显著性 P 值。
* **任务 2.2：局部莫兰散点图 (Local Moran's I Scatter Plot)**：绘制四个象限（高-高集聚、低-低集聚等），直观展示哪些省份构成了碳排放或数字化的“抱团区”。
* **产出**：`02_spatial_autocorrelation.py` (生成全局莫兰指数表格和局部散点图)。

#### 阶段三：模型甄别与参数估计 (SDM Estimation)

SDM 的一般数学表达为：

$$
Y_{it} = \rho \sum_{j=1}^N W_{ij} Y_{jt} + \beta X_{it} + \theta \sum_{j=1}^N W_{ij} X_{jt} + \mu_i + \lambda_t + \epsilon_{it}
$$

*其中 $\rho$ 是空间自回归系数，$\beta$ 是本地效应，$\theta$ 是空间交互效应（邻居变量对本地的影响）。*

* **任务 3.1：模型退化检验 (Wald / LR test)**：
  * 检验 $H_0: \theta = 0$，看 SDM 是否可以退化为空间滞后模型 (SAR)。
  * 检验 $H_0: \theta + \rho \beta = 0$，看 SDM 是否可以退化为空间误差模型 (SEM)。
  * *注：一般来说，SDM包含更为丰富的信息，不论检验结果如何，目前顶刊多倾向于直接保留 SDM。*
* **任务 3.2：固定效应选择**：执行 Hausman 检验确定是否使用固定效应。基于项目特性，我们依然锁定 **双向固定效应 (TWFE-SDM)**。
* **产出**：`03_baseline_sdm_regression.py`（输出模型比较和基准回归表）。

#### 阶段四：关键！空间效应分解 (Effect Decomposition)

**注意：在空间杜宾模型中，由于存在空间反馈循环（如果本省改变，会影响邻居，邻居进而又反作用于本省），回归系数 $\beta$ 并不等于真实的边际效应！**
必须使用偏微分方法计算三种效应，这是 SDM 最核心的看点：

* **直接效应 (Direct Effect)**：本省数字化对本省碳排放的真实影响（包含反馈效应）。
* **间接效应/空间溢出效应 (Indirect / Spillover Effect)**：本省数字化对邻近省份碳排放的影响，或者邻居的数字化对本省的影响。这是传统 TWFE 完全无法观测到的。
* **总效应 (Total Effect)**：直接效应 + 间接效应。
* **产出**：在 `03_baseline_sdm_regression.py` 中补充计算效应分解。

#### 阶段五：模型拓展与稳健性 (Robustness & Extension)

直接平移引申 project_v1 已经做过的稳健性内容：

* **任务 5.1**：替换核心因变量（碳排放强度 -> 人均碳排放）。
* **任务 5.2**：更换空间权重矩阵（如从邻接矩阵换成经济矩阵）。
* **任务 5.3**：控制内生性（空间工具变量估计 GS2SLS 或系统 GMM）。
* **产出**：`04_spatial_robustness.py`

---

### 💻 Python 技术栈评估

在使用 Python 进行面板空间计量时，需要注意生态圈工具的成熟度。
传统的 `statsmodels` 不支持空间计量。我们将采用专门的空间数据科学包组合：

* **`libpysal`**: 用于构建各种空间权重矩阵 $W$。
* **`esda`** (Exploratory Spatial Data Analysis): 用于计算全局与局部 Moran's I。
* **`spreg`** (Spatial Regression) 或非官方库包：虽然 `spreg` 主要是截面数据，针对**面板数据**的空间杜宾模型（Panel SDM），如果 Python 包局限性较大，我们需要自己通过最大似然估计（MLE）编写相关矩阵运算，或者使用更先进的 Python 面板库如 `linearmodels` 的扩展。或者，如果是高度学术化需求，业界也常常在这个特定步骤结合 Stata (`xsmle`) 或 R (`splm`)，但我们可以完全**基于 Python 的 `scipy.optimize` 构建严谨的面板 SDM MLE 似然函数**。这是我作为技术系统架构师可以为你搞定的硬核。

### 接下来？

如果你对这个整体方案（**空间权重 -> 莫兰检验 -> SDM 模型挑选 -> 效应分解 -> 稳健性**）没有异议，我们的**第一步就是寻找/构建省份的经纬度数据并生成空间权重矩阵**。

你是否同意启动第一步任务：**生成 $0-1$ 邻接矩阵与地理距离矩阵（编写 `project_v2/code/01_spatial_weights.py`）**？
