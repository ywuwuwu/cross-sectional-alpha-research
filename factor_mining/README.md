# Day 11: 多因子策略回测系统

## 📚 项目概述

本项目是一个模块化、可扩展的量化回测框架，基于 Python 构建，支持多种因子策略的回测验证。

**核心特点**：
- ✅ 面向对象设计，模块解耦，易于扩展新策略
- ✅ 支持日频 / 月度调仓（month_start / month_end / N日）
- ✅ 完整的因子计算、预处理、中性化流程
- ✅ 分组回测与多空收益分析
- ✅ IC/ICIR 等专业评估指标
- ✅ 内置股票池过滤（ST、停牌、涨跌停、流动性）

**已实现的策略**：

| 策略 | 文件 | 核心逻辑 |
|------|------|---------|
| **UBL** | `ubl_strategy.py` | K线形态（上影线/实体/下影线）+ 威廉指标 |
| **UTR** | `utr_strategy.py` | 换手率水平 + 换手率波动的综合排名 |
| **Ideal Reversal** | `ideal_reversal_strategy.py` | 按成交金额切割收益率，捕捉机构资金动向 |
| **CPV** | `cpv_strategy.py` | 日内收盘价与成交量的相关系数（真正的价量相关） |

---

## 🏗️ 架构设计

### 设计模式：策略模式 + 外观模式

```
┌─────────────────────────────────────────────────────────┐
│                    BacktestEngine                        │
│                    (回测引擎 - 外观)                      │
└──────────────┬──────────────┬──────────────┬─────────────┘
               │              │              │
       ┌───────▼──────┐ ┌─────▼─────┐ ┌─────▼──────────┐
       │ DataLoader   │ │ Portfolio │ │  Performance   │
       │ (数据加载)   │ │ Manager   │ │  Evaluator     │
       │              │ │ (组合管理)│ │  (绩效评估)    │
       └──────────────┘ └───────────┘ └────────────────┘
               │
       ┌───────▼──────┐
       │  Strategy    │◄──── 具体策略（UBL / UTR / CPV / IdealReversal）
       │  (策略基类)  │
       └──────────────┘
```

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| **回测引擎** | `backtest_engine_strategy.py` | 统一调度，串联各模块 |
| **数据加载器** | `data_loader.py` | 加载行情、状态、收益数据 |
| **策略基类** | `strategy_base.py` | 定义策略接口（calculate_factor + generate_signal） |
| **组合管理器** | `portfolio_manager.py` | 管理持仓、资金、交易成本 |
| **绩效评估器** | `performance_evaluator.py` | 计算收益、夏普、回撤、IC等 |

---

## 🚀 新手指南：5分钟上手回测

### 步骤1：准备环境

```bash
# 确保安装了必要的包
pip install numpy pandas scipy matplotlib statsmodels
```

### 步骤2：准备数据

项目需要以下数据目录结构：

```
data/
├── data_daily/          # 日频行情数据（open, close, high, low, volume, money, turnover_ratio）
├── data_ret/            # 收益率数据（1vwap_pct, 5vwap_pct, 10vwap_pct）
├── data_ud_new/         # 交易状态数据（paused, zt, dt, st）
├── data_barra/          # Barra风格因子（可选，用于中性化）
├── data_industry/       # 行业分类数据（可选，用于行业中性化）
├── data_5m/             # 5分钟数据（仅CPV策略需要）
└── date.pkl             # 交易日列表
```

### 步骤3：运行回测

有三种方式可以运行回测，选择适合你的：

#### 方式A：直接运行策略文件（最简单，适合快速测试）

每个策略文件底部都自带测试代码，直接运行即可：

```bash
# 在项目根目录（Factor/）下运行
conda run -n factor python3 src/ubl_strategy.py
conda run -n factor python3 src/utr_strategy.py
conda run -n factor python3 src/ideal_reversal_strategy.py
conda run -n factor python3 src/cpv_strategy.py
```

**⚠️ 注意**：策略文件中的数据路径为 `./data/`，因此需要在项目**根目录**运行，而非 `src/` 目录下。

#### 方式B：运行回测引擎（测试示例策略）

```bash
conda run -n factor python3 backtest_engine_strategy.py
```

这会运行回测引擎自带的示例（动量策略 + 反转策略）。

#### 方式C：自己写脚本（最灵活，推荐用于正式回测）

```python
from backtest_engine_strategy import BacktestEngine
from utr_strategy import UTRStrategy  # 换成你想测试的策略

# 1. 配置引擎
engine = BacktestEngine(
    data_dir='./data',
    initial_capital=1_000_000,    # 初始资金100万
    commission_rate=0.0003,       # 万三佣金
    slippage_rate=0.001,          # 千一滑点
    stamp_duty=0.001,             # 千一印花税
    risk_free_rate=0.03,          # 3%无风险利率
)

# 2. 创建策略
strategy = UTRStrategy(data_dir='./data')

# 3. 运行回测
report = engine.run(
    start_date='2020-01-02',
    end_date='2022-01-21',
    strategy=strategy,
    top_n=50,                     # 选50只股票
    rebalance_freq='month_start', # 每月初调仓
    enable_cost=True,             # 计算交易成本
    calculate_ic=True,            # 计算IC指标
    n_groups=5,                   # 分5组回测
)

# 4. 查看报告
engine.print_report(report)
```

**保存为 `run_backtest.py`，然后运行：**
```bash
conda run -n factor python3 run_backtest.py
```

---

### 📅 如何指定回测范围？

回测范围通过 `start_date` 和 `end_date` 参数控制：

```python
report = engine.run(
    start_date='2020-01-02',   # 回测开始日期
    end_date='2022-01-21',     # 回测结束日期
    strategy=strategy,
    top_n=50,
    rebalance_freq='month_start',
    enable_cost=True,
    calculate_ic=True,
    n_groups=5,
)
```

**各策略的数据覆盖范围：**

| 策略 | 可用日期范围 | 说明 |
|------|-------------|------|
| UBL / UTR / Ideal Reversal | 2020-01-02 ~ 2022-01-21 | 日频数据覆盖2年 |
| CPV | 2021-01-04 ~ 2021-12-31 | 5分钟数据仅覆盖2021年 |

**⚠️ 注意事项：**
- 日期必须是交易日（周末和节假日会自动跳过）
- CPV策略需要20天历史数据计算滚动窗口，因此最早回测日期是 **2021-01-29**
- 如果指定的日期没有数据，回测会返回空结果

**快速测试建议（缩短回测时间）：**
```python
# 只回测3个月（快速验证）
start_date='2020-03-01'
end_date='2020-06-01'

# 只回测1个月（最快验证）
start_date='2020-03-01'
end_date='2020-03-31'
```

---

### 步骤4：切换其他策略

只需修改导入的策略类，其他代码完全不变：

```python
# UBL策略
from src.ubl_strategy import UBLStrategy
strategy = UBLStrategy(data_dir='./data')

# UTR策略
from src.utr_strategy import UTRStrategy
strategy = UTRStrategy(data_dir='./data')

# Ideal Reversal策略
from src.ideal_reversal_strategy import IdealReversalStrategy
strategy = IdealReversalStrategy(data_dir='./data')

# CPV策略（.py文件版，单线程）
from src.cpv_strategy import CPVStrategy
strategy = CPVStrategy(data_dir='./data', min5_dir='./data/data_5m')
```

---

#### 方式D：CPV 策略 - Jupyter Notebook（Ray 并行优化，推荐）

CPV 策略由于需要读取大量 5 分钟数据文件，计算量较大。我们提供了 **Ray 并行优化版 Notebook**：

```bash
# 启动 Jupyter Notebook
conda run -n factor jupyter notebook src/cpv_ray_optimized.ipynb
```

**为什么用 Notebook？**

| 运行方式 | 并行支持 | 原因 |
|----------|----------|------|
| `cpv_strategy.py` | ❌ 单线程 | Ray worker 进程无法找到模块导入路径 |
| `cpv_ray_optimized.ipynb` | ✅ Ray 并行 | Notebook 中所有代码在同一个交互式环境，无模块导入问题 |

**Notebook 内容**：
- 内嵌完整的 CPV 策略 + 回测引擎（零外部依赖）
- Ray 并行计算每日 close-volume 相关系数
- 性能对比：Ray 并行 vs 单线程
- 完整回测示例 + 净值曲线可视化

**数据路径**：Notebook 中的路径为 `../data/`（因为 Notebook 在 `src/` 目录下运行）。

---

## ⚡ 性能优化

### 各策略并行化状态

| 策略 | 并行方式 | 状态 | 说明 |
|------|----------|------|------|
| **UBL** | - | 单线程 | pandas 向量化操作已足够高效 |
| **UTR** | - | 单线程 | rolling + rank 为向量化运算，多进程收益有限 |
| **Ideal Reversal** | `multiprocessing.Pool(4)` | ✅ 已启用 | 每只股票独立计算，适合多进程 |
| **CPV (.py)** | - | 单线程（自动回退） | Ray 在模块化 .py 中有模块导入问题 |
| **CPV (.ipynb)** | `Ray` (4 CPU) | ✅ 已启用 | Notebook 环境中 Ray 可正常工作 |

### Ideal Reversal 多进程优化

```python
# 默认启用多进程，4个worker
strategy = IdealReversalStrategy(
    data_dir='./data',
    use_multiprocessing=True,  # 默认True
    num_workers=4,             # 默认4进程
)

# 如果多进程失败，自动回退到单线程
```

### CPV Ray 并行优化（仅 Notebook）

```python
# 在 cpv_ray_optimized.ipynb 中
strategy = CPVStrategy(
    data_dir='../data',
    min5_dir='../data/data_5m',
    use_ray=True,      # 启用 Ray
    ray_cpus=4,        # 使用4个CPU核心
)
```

### 性能对比参考

| 策略 | 单线程 | 并行 | 加速比 | 备注 |
|------|--------|------|--------|------|
| Ideal Reversal | ~15s | ~5.6s | **~2.7x** | 3400+只股票 |
| CPV (Ray) | ~3s/天 | ~1s/天 | **~3x** | 取决于数据量 |

---

## 💡 各策略详解

### 1. UBL 策略（K线形态因子）

**核心思想**：通过量化蜡烛图形态特征（上影线、实体、下影线）和威廉指标，捕捉价格行为模式。

**因子构成**：
```python
U = 上影线长度 / K线总长度    # 上方抛压
B = 实体长度 / K线总长度      # 波动剧烈程度
L = 下影线长度 / K线总长度    # 下方支撑
WR = (Close - Low) / (High - Low) * 100   # 威廉指标
TREND = WR短期均值 - WR长期均值            # 趋势方向

UBL = w1*U + w2*B + w3*L + w4*WR + w5*TREND
```

**经济学含义**：
- U高 → 上方抛压重 → 可能下跌
- L高 → 下方支撑强 → 可能上涨
- WR > 80 → 超买 → 可能反转下跌
- TREND > 0 → 短期强于长期 → 动量向上

**关键参数**：
```python
UBLStrategy(
    candle_window_short=5,   # 短期K线窗口
    candle_window_long=20,   # 长期K线窗口
    wr_window_short=5,       # 短期威廉窗口
    wr_window_long=20,       # 长期威廉窗口
    neutralize_industry=True, # 是否行业中性化
)
```

---

### 2. UTR 策略（优加换手率因子）

**核心思想**：结合换手率水平和换手率波动，通过排名组合筛选股票。

**因子构成**：
```python
Turn20 = mean(turnover_ratio, 20)   # 20日平均换手率
STR = std(turnover_ratio, 20)       # 20日换手率标准差

# 排名组合
score1 = STR 的截面排名
if STR 排名前50%（高波动）:
    score2 = Turn20 的反向排名（换手越低越好）
else:
    score2 = Turn20 的正向排名（换手越高越好）

UTR = score1 + score2
```

**经济学含义**：

| 情况 | 解释 | 选股逻辑 |
|------|------|---------|
| 高波动 + 低换手 | 筹码趋于集中 | ✅ 看好 |
| 高波动 + 高换手 | 投机氛围重 | ❌ 回避 |
| 低波动 + 高换手 | 流动性好 | ✅ 看好 |
| 低波动 + 低换手 | 冷门股 | ❌ 回避 |

**关键参数**：
```python
UTRStrategy(
    turnover_window=20,   # 换手率计算窗口
    neutralize=True,      # 是否对UTR中性化
)
```

---

### 3. Ideal Reversal 策略（因子切割）

**核心思想**：根据成交金额大小切割收益率，区分机构资金和散户资金的贡献。

**因子构成**：
```python
# 20日滚动窗口
M_high = 成交金额最高的10天的收益率之和  # 机构行为
M_low = 成交金额最低的10天的收益率之和   # 散户行为

ideal_reverse = M_high - M_low
```

**经济学含义**：
- ideal_reverse > 0：大额交易时涨得多 → 机构在买入 → 可能继续上涨
- ideal_reverse < 0：大额交易时跌得多 → 机构在卖出 → 可能继续下跌

**关键参数**：
```python
IdealReversalStrategy(
    window=20,        # 滚动窗口
    top_n_days=10,    # 取高/低成交金额的天数
)
```

---

### 4. CPV 策略（真正的价量相关性因子）

**核心思想**：计算日内收盘价与成交量的相关系数，捕捉价量关系模式。

**因子构成**：
```python
# 每天从5分钟数据计算
close_volume_corr = corr(close_5min, volume_5min)  # 日内相关系数

PV_corr_avg = mean(close_volume_corr, 20)   # 20日滚动均值
PV_corr_std = std(close_volume_corr, 20)    # 20日滚动标准差

CPV = zscore(PV_corr_avg) + zscore(PV_corr_std)
```

**经济学含义**：
- 正相关：价格上涨伴随放量 → 趋势确认 → 可能继续上涨
- 负相关：价格上涨但缩量 → 趋势可疑 → 可能反转

**⚠️ 重要限制**：
- 需要 `data/data_5m/` 目录（5分钟级别数据）
- 5分钟数据仅覆盖 **2021年**，因此回测区间受限
- 建议回测区间：`start_date='2021-01-29', end_date='2021-12-31'`

**关键参数**：
```python
CPVStrategy(
    min5_dir='./data/data_5m',  # 5分钟数据目录
    corr_window=20,             # 相关系数滚动窗口
)
```

---

## 📊 回测流程

```
开始回测
    ↓
1. 初始化
   ├─ 加载数据（交易日列表）
   ├─ 初始化组合管理器（资金、持仓）
   └─ 初始化绩效评估器
    ↓
2. 逐日回测循环 [for date in backtest_dates]
    ↓
    ┌──────────────────────────────────────┐
    │  T日 (date)                           │
    ├──────────────────────────────────────┤
    │ 开盘 → 执行前一日信号调仓             │
    │ 盘后 → 结算当日收益                   │
    │ 盘后 → 计算因子 / IC / 分组收益       │
    │ 盘后 → 若为调仓日，生成次日信号       │
    └──────────────────────────────────────┘
    ↓
3. 汇总统计 → 生成绩效报告
    ↓
结束回测
```

**关键时间点**（避免未来函数）：
- **T日收盘**：用T日及之前的数据计算因子
- **T+1日开盘**：执行调仓（买入/卖出）
- **T→T+1收益**：持仓的实际收益

---

## 📈 绩效指标解读

| 指标 | 含义 | 评判标准 |
|------|------|---------|
| **年化收益率** | 平均每年赚多少 | > 10% 优秀 |
| **最大回撤** | 最多亏多少 | < 20% 可接受 |
| **夏普比率** | 每单位风险赚多少 | > 1.0 优秀 |
| **IC均值** | 因子预测能力 | > 0.03 有效，> 0.05 优秀 |
| **ICIR** | IC稳定性 | > 1.5 稳健 |
| **IC胜率** | IC>0的比例 | > 55% 有效 |
| **多空收益** | 多头组 - 空头组 | > 0 因子有效 |

---

## ⚙️ 参数调优建议

### 调仓频率

| 频率 | 参数 | 适用场景 | 成本 |
|------|------|---------|------|
| 日频 | `1` | 高频策略 | 高 |
| 周频 | `5` | 短期策略 | 中 |
| **月频** | **`'month_start'`** | **因子选股（推荐）** | **低** |
| 季频 | `60` | 基本面策略 | 最低 |

### 选股数量

| 数量 | 风险 | 收益 |
|------|------|------|
| 10-20 | 高 | 高 |
| **30-50** | **中（推荐）** | **中** |
| 100+ | 低 | 低 |

---

## ⚠️ 常见问题

### Q1: 回测结果为空？
- 检查 `data/` 目录是否存在且数据完整
- 检查回测日期是否在数据覆盖范围内
- CPV策略需要5分钟数据，只能回测2021年

### Q2: `FileNotFoundError: data/date.pkl`？
- **原因**：在 `src/` 目录下运行了策略文件，但路径是 `./data/`
- **解决**：在项目**根目录**运行：`conda run -n factor python3 src/xxx_strategy.py`
- **CPV Notebook**：在 `src/` 下运行，路径已设为 `../data/`

### Q3: IC为负？
- 可能是因子方向反了，尝试 `ascending=True` 选股
- 也可能是因子本身与收益负相关

### Q4: 换手率过高？
- 尝试降低调仓频率（从日频改为月频）
- 增加持仓粘性设计（如只换出跌出前80%的股票）

### Q5: CPV 策略 .py 文件为什么不用 Ray？
- **原因**：Ray worker 进程无法导入 `cpv_strategy` 模块（`ModuleNotFoundError`）
- **解决**：使用 `cpv_ray_optimized.ipynb`，Notebook 环境无此问题
- **回退**：`.py` 版本会自动回退到单线程，功能正常

### Q6: 如何添加新策略？
1. 创建新文件 `my_strategy.py`
2. 继承 `Strategy` 基类
3. 实现 `calculate_factor(date, data_loader)` 方法
4. 实现 `generate_signal(factor_df, top_n)` 方法
5. 参考现有策略的缓存机制和股票池过滤

---

## 📝 版本历史

### v2.1 (2026-05-26)
- ✅ Ideal Reversal 策略添加 `multiprocessing.Pool(4)` 多进程并行优化
- ✅ CPV 策略添加 Ray 并行优化（`cpv_ray_optimized.ipynb`）
- ✅ CPV `.py` 版本添加自动回退机制（Ray失败则单线程）
- ✅ 新增 `cpv_ray_optimized.ipynb`（内嵌完整回测引擎，零外部依赖）
- ✅ 更新 README：新增性能优化章节、Notebook运行方式、常见问题

### v2.0 (2025-05-26)
- ✅ 新增 UTR 策略（优加换手率）
- ✅ 新增 Ideal Reversal 策略（因子切割）
- ✅ 新增 CPV 策略（真正的价量相关性，需5分钟数据）
- ✅ 统一策略接口，所有策略适配 BacktestEngine
- ✅ 优化 README，新增详细新手指南

### v1.0 (2024-02-03)
- ✅ 实现 UBL 因子策略
- ✅ 完整回测框架
- ✅ IC/ICIR计算
- ✅ 市值中性化
- ✅ 月频调仓测试

---

## Research Runner: parameter sweeps and reports

Use `run_research_backtest.py` when you want to compare strategies or tune parameters without editing Python files by hand. Root-level `visualizer.py` mirrors the plotting/results blocks from `day11.ipynb` and embeds them into each report. Run it from the lesson root, one level above `factor_mining/`:

```bash
python run_research_backtest.py --strategy utr --start 2021-03-01 --end 2021-12-31 --top-n 50 --rebalance-freq month_start
```

Grid search example:

```bash
python run_research_backtest.py --strategy utr --start 2021-03-01 --end 2021-12-31 \
  --grid-param turnover_window=10,20,40 --grid-param top_n=30,50,100 \
  --rebalance-freq month_start
```

Supported strategies: `ubl`, `paper_ubl` (`PaperUBL_Strategy.py` strict report formula), `utr`, `ideal_reversal`, `cpv`, `momentum`, `reversal`.

Useful knobs:
- `--strategy-param key=value`: pass one strategy constructor parameter. Repeat it as needed.
- `--grid-param key=v1,v2`: sweep strategy or engine parameters. Repeat it for Cartesian-product grids.
- Engine grid keys include `top_n`, `rebalance_freq`, `enable_cost`, `n_groups`, `commission_rate`, `slippage_rate`, `stamp_duty`, `risk_free_rate`.
- Outputs are saved under `reports/<strategy>_<timestamp>/` with `summary.csv`, per-run `report.md`, metrics JSON, return series, IC series, group returns, and plots unless `--no-plots` is set.
