# SimpleQuant - 入门量化交易项目

一个结构清晰、适合初学者理解的量化交易框架。

## 项目结构

```
new_quant/
├── config/           # 配置
├── data/             # 数据存储
├── strategy/         # 策略模块
├── backtest/         # 回测引擎
├── utils/            # 工具函数
├── visualization/    # 可视化
└── main.py           # 入口
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行示例

```bash
python main.py
```

## 核心模块说明

- **数据获取 (utils/data_fetcher.py)**: 使用 yfinance 获取股票历史数据
- **策略 (strategy/sma_strategy.py)**: 简单双均线交叉策略示例
- **回测引擎 (backtest/engine.py)**: 基于向量化计算的回测框架
- **可视化 (visualization/plotter.py)**: 使用 matplotlib 绘制净值曲线和交易信号

## 自定义策略

在 `strategy/` 目录下新建文件，继承 `BaseStrategy`，实现 `generate_signals` 方法即可。
