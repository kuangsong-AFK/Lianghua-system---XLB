# 小吕布量化 Pro (Lianghua-system — XLB)

一个基于 Streamlit 的**零代码 / 低代码智能量化投研终端**：把「AI 生成交易策略 → 沙盒安全校验 → 历史回测 → 全市场选股 → 深度学习预测 → 期货审计」串成一条完整链路。

> ⚠️ 本项目仅供学习与研究使用，不构成任何投资建议。量化交易存在风险，请勿据此实盘操作。

## ✨ 核心功能

| 模块 | 说明 |
| --- | --- |
| 🏠 系统总览 | 平台监控中控与简介 |
| 🤖 AI 策略引擎 (LLM) | 接入 Kimi / Moonshot，自然语言生成策略代码；支持 PDF / Word / CSV / 图片多模态附件 |
| 💻 极客量化 IDE | 策略代码编辑器 + 经典模板 + 沙盒测试 + 密码存档室 |
| 📈 深度静态回测 | 长达 10 年历史回测，含胜率 / 夏普 / 最大回撤归因 |
| 🔍 选股神器 | 复用当前策略代码，全市场多线程扫描买点 |
| ⚡ 实时高频交易 | 逐 K 线信号推演 |
| 🧠 深度学习预测 | LSTM / GRU / 1D-CNN 在线训练，推演未来 5 天价格 |
| 🔗 期货全量审计 | 基于 AkShare 的期货多空回测（保证金 / 乘数计算，接口失败自动模拟兜底） |
| 🌪️ 期货高频沙盘 | Tick 级盘口模拟推演 |

## 🏗️ 项目结构

```
Lianghua-system---XLB-main/
├── app.py                       # Streamlit Cloud 入口（转投 DL_Quant_System/app.py）
├── requirements.txt             # 依赖清单
├── start.bat                    # 本地一键启动（自动寻路）
├── 手机版.bat                   # 局域网手机访问模式
└── DL_Quant_System/
    ├── app.py                   # 主应用（所有页面）
    ├── strategy_sandbox.py      # 策略代码 AST 白名单沙盒（安全核心）
    ├── backtester/engine.py     # 向量化回测引擎
    ├── screener.py              # 全市场选股扫描
    ├── data_loader.py           # 数据源：Tushare 优先、本地 CSV 兜底
    ├── ai_prompts.py            # AI 策略生成提示词（10 条军规）
    ├── extensions.py            # IDE / 期货 / 3D 桌宠等扩展页
    ├── strategy_templates.py    # 内置策略模板（缠论 / 海龟 / TTM / 自适应 RSI）
    ├── strategy_store.py        # 策略本地存档（JSON）
    ├── bg_runner.py             # 后台任务运行器（异步 + 可停止）
    └── models/ data/ static/    # 模型权重 / 样例行情 / 3D 资产
```

## 🚀 本地运行

1. 准备 Python 3.11 虚拟环境（项目默认 `.venv`）：

   ```bash
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```

2. 配置密钥（二选一）：
   - 在项目根目录 `.streamlit/secrets.toml` 写入：
     ```toml
     KIMI_API_KEY = "sk-..."
     TUSHARE_TOKEN = "your-token"
     ```
   - 或复制 `.env.example` 为 `.env` 并填写。
3. 启动：

   ```bash
   .venv\Scripts\python -m streamlit run DL_Quant_System\app.py
   ```

   或直接双击 `start.bat`；手机在同一 WiFi 下可用 `手机版.bat` 远程访问。

> 没有 Tushare Token 也可以运行：系统会自动回退到 `DL_Quant_System/data/` 下的本地 CSV 样例数据。

## ☁️ Streamlit Cloud 部署

- 入口文件：根目录 `app.py`。
- 在应用 Settings → Secrets 中填入 `KIMI_API_KEY` 与 `TUSHARE_TOKEN`。
- 注意：`torch` 默认安装 CUDA 版体积较大，若超出云端包体积限制，可改用 CPU 版 wheel（`--index-url https://download.pytorch.org/whl/cpu`）。

## 🔐 策略 SDK 军规（约束 AI / IDE 生成的代码）

沙盒（`strategy_sandbox.py`）通过 AST 白名单执行策略代码，规则如下：

- 入口函数必须严格为 `def generate_signals(df):`，且只能定义这一个函数；
- 禁止 `import` / `for` / `while` / `try` / `lambda` / `class` / 装饰器；
- 数据列名：`Open` / `High` / `Low` / `Close` / `Volume`（`Volume` 可能不存在，需用 `df.get('Volume', 0)`）；
- 必须返回含整数 `Signal` 列（`1` 买 / `-1` 卖 / `0` 持有）的 DataFrame，行数不变；
- 画图列：主图用 `MAIN_` 前缀，副图用 `SUB1_` / `SUB2_` 前缀；
- 逻辑比较用 `&` / `|` / `~` 并加括号，避免未来函数（用 `shift(1)` 取历史值）。

## 📚 备注

- `DL_Quant_System/main.py` 为早期遗留的独立流水线（Matplotlib 研报生成），已不在主流程中使用。
- `DL_Quant_System/models/lstm_model.py` 依赖 TensorFlow，为旧版 LSTM 实现；当前主流程的深度学习改用 PyTorch（见「深度学习预测矩阵」页），TensorFlow 不在依赖清单中。
- 策略存档密码：`688688`（存档文件已加入 `.gitignore`，不会上传）。

## 📄 版权

私有项目，保留所有权利。
