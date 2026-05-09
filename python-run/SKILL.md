---
name: python-run
description: >
  This skill should be used when the user wants to run Python commands or .py files,
  OR when the user wants to explain/parse Python code without running it.
  It locates a Python interpreter on the system, executes the provided code or
  .py file, captures stdout/stderr output, and produces a structured analysis
  report covering commands executed, output results, exceptions, warnings,
  and performance. It also supports an "explain mode" that parses Python code
  line-by-line (merging trivial/loop lines) and produces a structured explanation
  and overall evaluation without executing anything.
---

# python-run Skill

Run Python commands / `.py` files and analyze results, **or** explain Python code without running it.

---

## When to Use

Load this skill when the user:
- Asks to **run** one or more Python statements or a code snippet
- Asks to **execute** an existing `.py` file in the workspace
- Wants to know what the output / result of some Python code is
- Needs to install a package and then run code
- Asks to **explain**, **解释**, **解读**, **逐行分析** Python code or a `.py` file **without running**
- Uses phrases like "这段代码是什么意思", "帮我看看这个py文件", "不运行，只解释", "这个脚本做了什么"

---

## Mode A — Run & Report（执行模式）

### Step 1 — Locate Python Interpreter

Try the following in order until one succeeds:

```powershell
# 1. Check workspace-level virtual env
Test-Path ".\venv\Scripts\python.exe"
Test-Path ".\.venv\Scripts\python.exe"

# 2. Check PATH
Get-Command python -ErrorAction SilentlyContinue
Get-Command python3 -ErrorAction SilentlyContinue

# 3. Check common installation paths (Windows)
Test-Path "C:\Python312\python.exe"
Test-Path "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
Test-Path "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
```

Or let the helper script auto-detect:

```bash
python scripts/run_python.py --file <path> --timeout 60
```

### Step 2 — Prepare the .py file

**Case A — User provides code in chat:**

Write a temporary `.py` file (e.g., `E:\AI\test\run_python_tmp.py`) containing:
1. Each statement on its own line, preserving original indentation
2. No extra `exit()` needed — the script terminates naturally

**Case B — User points to an existing `.py` file:**

Use the file as-is.

### Step 3 — Execute

**Option 1 — Direct execution via PowerShell:**

```powershell
& python "E:\AI\test\run_python_tmp.py" 2>&1
```

**Option 2 — Via bundled helper script (recommended for structured output):**

```bash
# Execute a .py file
python scripts/run_python.py --file "E:\AI\test\run_python_tmp.py" --timeout 60

# Execute inline code lines
python scripts/run_python.py --code "import math" "print(math.pi)"

# Specify a custom interpreter
python scripts/run_python.py --file "script.py" --python "C:\Python312\python.exe"
```

Helper script location: `scripts/run_python.py` (in this skill's directory)

### Step 4 — Analyze and Report

| 项目 | 说明 |
|------|------|
| **执行状态** | 是否成功（returncode == 0 为成功） |
| **标准输出** | `print()` 及其他 stdout 内容 |
| **标准错误** | 异常 traceback、`warnings.warn` 等 |
| **异常类型** | 从 stderr 中提取 `ErrorType: message` |
| **耗时** | 脚本执行时间（秒） |
| **依赖检查** | 是否有 `ModuleNotFoundError`，提示安装命令 |
| **输出文件** | 脚本中 `open(..., 'w')` / `savefig` 等生成的文件路径 |
| **变量/结果** | 若脚本输出了 DataFrame、统计量等，汇总关键数值 |

### Key Conventions

- Always save generated files to the workspace (`E:\AI\test\`) unless the user specifies otherwise
- If a `ModuleNotFoundError` occurs, propose: `pip install <module>` and offer to re-run
- For long-running scripts, set `--timeout 60` (default); for data-heavy tasks, increase to 120+
- Temporary `.py` files can be deleted after successful execution unless the user asks to keep them
- If the script produces matplotlib/plotly figures, add `plt.savefig(...)` before `plt.show()` to export as PNG

### Error Handling

| 错误特征 | 可能原因 | 处理建议 |
|----------|----------|----------|
| `ModuleNotFoundError` | 缺少第三方包 | `pip install <module>` 后重试 |
| `SyntaxError` | 代码语法错误 | 定位出错行，修正后重试 |
| `FileNotFoundError` | 路径错误 | 检查文件路径，使用绝对路径 |
| `IndentationError` | 缩进不一致 | 统一使用 4 空格或 Tab，不可混用 |
| `PermissionError` | 文件权限不足 | 检查目标路径写权限 |
| `TimeoutExpired` | 脚本执行超时 | 增大 `--timeout`，或检查是否有死循环 |
| returncode ≠ 0 | 运行时异常 | 读取 stderr 中的 traceback 定位问题 |

---

## Mode B — Explain（代码解析模式）

> **触发条件**: 用户明确表示"不运行/只解释/帮我看看/这是什么意思"，或提供代码但未要求执行时。

**不执行任何命令**，仅对代码进行静态分析和解释。

### 解析规则

1. **逐段解释**：将代码按逻辑分块（导包、数据读取、数据处理、计算、可视化、输出等），每块给出统一解释，而非机械地每行一条。
2. **合并处理以下情形**：
   - 循环体（`for` / `while`）：整体解释循环逻辑，不逐行展开
   - 连续的赋值 / 变量生成语句且目的相同：合并为一条说明
   - 连续的 `plt.xxx()` 图形绘制/设置命令：合并为"图形绘制/美化"一条
   - 连续的 `import` / `from ... import` 语句：合并说明导入了哪些库及其用途
   - 连续的 `print()` / `logging` 等输出语句：合并说明输出内容
3. **注释行**（`#` 开头）：与紧随其后的代码块合并解释，说明注释意图是否与代码一致。
4. **命令格式统一**：每个解释块输出为固定格式，包含：
   - 代码片段（原始，可多行）
   - 功能说明（用中文，简洁）
   - 关键参数说明（若有函数参数、选项等值得说明的，逐一列出）

### 输出格式

输出分两部分：

#### 第一部分：逐块解释

```
### [序号] [功能概括标题]

**代码：**
```python
<原始代码块>
```

**解释：**
<功能描述，1-3句话>

**关键参数：**
- `参数名`: 说明
```

对于简单语句，可以省略"关键参数"小节。

#### 第二部分：总结评价

| 评价维度 | 内容 |
|----------|------|
| **代码目的** | 用1-2句话概括整段代码的总体目标 |
| **数据流向** | 数据从哪里来 → 经过哪些变换 → 输出到哪里 |
| **技术亮点** | 值得学习或巧妙的写法（如有） |
| **潜在问题** | 可能出错的地方、兼容性风险、性能隐患等（如有） |
| **改进建议** | 可选，如有更简洁/健壮/Pythonic 的写法可提出 |

### 解析示例

**用户输入：**
> 帮我解释这段代码（不需要运行）：
> ```python
> import pandas as pd
> df = pd.read_csv("data.csv")
> df["log_price"] = df["price"].apply(lambda x: x ** 0.5)
> print(df.describe())
> ```

**输出示例：**

---

### [1] 导入依赖库

**代码：**
```python
import pandas as pd
```
**解释：**
导入 pandas 数据分析库，并取别名 `pd`，用于后续的数据读取和操作。

---

### [2] 读取 CSV 数据

**代码：**
```python
df = pd.read_csv("data.csv")
```
**解释：**
从当前工作目录读取 `data.csv` 文件，加载为 pandas DataFrame，存入变量 `df`。

---

### [3] 生成价格开方变量

**代码：**
```python
df["log_price"] = df["price"].apply(lambda x: x ** 0.5)
```
**解释：**
对 `price` 列的每个值取平方根，生成新列 `log_price`（列名有误导性，实际是开方而非取对数）。

**关键参数：**
- `apply(lambda x: ...)`: 对每个元素应用匿名函数，等价于 `df["price"] ** 0.5`，但后者更简洁

---

### [4] 打印描述性统计

**代码：**
```python
print(df.describe())
```
**解释：**
输出 DataFrame 所有数值列的描述性统计（计数、均值、标准差、分位数等）。

---

#### 总结评价

| 评价维度 | 内容 |
|----------|------|
| **代码目的** | 读取 CSV 数据，对价格做平方根变换，输出统计摘要 |
| **数据流向** | CSV 文件 → DataFrame → 新增变换列 → 统计输出 |
| **技术亮点** | 链式操作简洁，`describe()` 快速了解数据分布 |
| **潜在问题** | 列名 `log_price` 误导（实际是 sqrt），`price` 含负值时开方会产生 NaN |
| **改进建议** | 改用 `df["sqrt_price"] = df["price"] ** 0.5`，更直接且无需 `apply` |

---







## Mode C — Time Series Cleaning（时间序列数据清洗）

> **触发条件**: 用户要求清洗原始时间序列数据、从日期中提取时间分量（年/月/季度）、删除非样本行（统计信息、元数据等）。

### Step 1 — 理解用户需求

与用户确认以下信息：
1. **原始数据文件**：Excel (.xlsx) 文件路径
2. **时间变量所在列**：默认 A 列
3. **数值变量所在列**：默认 B 列
4. **时间格式**：Excel 序列号（serial）还是日期字符串（string），留空则自动检测
5. **数据频率**：`daily` / `monthly` / `quarterly` / `yearly`
   - `daily` → 输出：**年份、季度、月份、日** + 数值
   - `monthly` → 输出：**年份、季度、月份** + 数值
   - `quarterly` → 输出：**年份、季度** + 数值
   - `yearly` → 输出：**年份** + 数值
6. **时间频率转换规则**：如"日度数据按年份和月份区分季度"，或用户自定义规则
7. **小数精度**：是否指定小数位数。默认自动检测——当一半以上数值有 n 位小数时，全部统一为 n 位

### Step 2 — 探查数据

先对文件做**快速探查**，了解结构和非样本行分布：

```bash
python scripts/ts_clean.py --input "<file.xlsx>" --probe
```

探查结果包含：
- **总行数**（含所有空行和统计信息行）
- **出现的列**（如 A 列、B 列）
- **首个有数据行**
- **最后一个有数据行**

根据探查结果判断数据起始位置和非样本行特征，必要时与用户确认。

### Step 3 — 执行清洗

**日度数据示例：**
```bash
python scripts/ts_clean.py \
  --input "<file.xlsx>" \
  --time-col "A" \
  --value-cols "B" \
  --value-names "iCPI" \
  --frequency daily
```

**季度数据示例：**
```bash
python scripts/ts_clean.py \
  --input "<file.xlsx>" \
  --time-col "A" \
  --value-cols "B,C,D" \
  --value-names "第一产业,第二产业,第三产业" \
  --frequency quarterly
```

参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | (必填) | 原始 xlsx 文件路径 |
| `--time-col` | `A` | 时间变量所在列字母 |
| `--value-col` | `B` | [已弃用] 单列数值，改用 --value-cols |
| `--value-cols` | `B` | 数值变量列字母列表，逗号分隔（如 "B,C,D"） |
| `--value-names` | `列X` | 数值变量名称列表，逗号分隔（如 "第一产业,第二产业,第三产业"） |
| `--time-format` | `auto` | 时间格式：`serial`(Excel序列号)、`string`(日期文本)、`auto`(自动检测) |
| `--frequency` | `daily` | 数据频率：`daily`(日度)、`monthly`(月度)、`quarterly`(季度)、`yearly`(年度) |
| `--decimal-places` | 自动 | 小数保留位数。不指定时自动检测：超半数样本的位数统一全表 |
| `--output-xlsx` | 自动生成 | 清洗后 xlsx 输出路径 |
| `--output-txt` | 自动生成 | 清洗流程说明输出路径 |
| `--probe` | - | 仅探查文件，不执行清洗 |

### Step 4 — 分析并报告

| 项目 | 说明 |
|------|------|
| **原始规模** | 原始 xlsx 总行数（含空行） |
| **非样本行** | 自动识别的统计信息/元数据/空行数量 |
| **有效观测** | 保留的样本观测值数量 |
| **数据频率** | 用户指定的频率（daily/monthly/quarterly/yearly） |
| **时间范围** | 清洗后的数据覆盖的时间范围（按频率显示） |
| **时间格式** | 检测到的时间格式类型 |
| **转换错误** | 时间变量转换失败的行数 |
| **输出变量** | 输出的变量列表（按频率自动生成） |
| **输出文件** | 清洗后的 xlsx 和清洗流程文档路径 |

### 非样本行自动识别规则

ts_clean.py 使用以下启发式规则判断一行是否为非样本行：

1. **全空行** → 非样本
2. **首列时间变量为空，但其他列有值** → 非样本（典型统计信息行）
3. **首列时间变量和数值列均有值** → 样本行（予以保留）

### 频率对应的输出变量

`--frequency` 参数决定输出的时间变量列数：

| 频率 | 输出变量 | 排序方式 |
|------|----------|----------|
| `daily` | 年份、季度、月份、日 + 数值 | 年→季→月→日 |
| `monthly` | 年份、季度、月份 + 数值 | 年→月 |
| `quarterly` | 年份、季度 + 数值 | 年→季 |
| `yearly` | 年份 + 数值 | 年 |

### 季度规则

采用统一的标准日历季度映射：

| 月份范围 | 对应季度 |
|----------|----------|
| 1 月 ~ 3 月 | 第 1 季度 |
| 4 月 ~ 6 月 | 第 2 季度 |
| 7 月 ~ 9 月 | 第 3 季度 |
| 10 月 ~ 12 月 | 第 4 季度 |

CEIC 数据库存储的季度数据（3/1、6/1、9/1、12/1）按此规则自然映射正确，无需额外规则。

### 小数精度统一规则

`ts_clean.py` 自动检测原始数据中数值的小数位数：

1. 扫描所有数值列的原始值（跳过整数，如 `100`、`137`）
2. 统计各小数位数出现的频次
3. 若某一位数的出现比例 **超过 50%**，则所有数值统一舍入到该位数
4. 若无超半数的情况，则采用出现最多的位数

例如：
- iCPI 数据中大多数值为 `99.9712`（4位）→ 全表统一 **4 位小数**
- GDP 数据中大多数值为 `528.49`（2位）→ 全表统一 **2 位小数**

可通过 `--decimal-places N` 手动指定位数，跳过自动检测。

### 错误处理

| 错误特征 | 可能原因 | 处理建议 |
|----------|----------|----------|
| `File not found` | 路径错误 | 检查文件路径拼写 |
| `No sheet1.xml` | 不是标准 xlsx | 确认文件格式 |
| 0 行保留 | 列名设置错误 | 重新确认 time-col/value-cols |
| 时间转换全部失败 | 格式不匹配 | 指定 `--time-format string` 或 `serial` |
| 季度数据但显示了日列 | 频率忘记设为 `quarterly` | 加上 `--frequency quarterly` |

## Mode D — Time Series Visualization（时间序列可视化）

> **触发条件**: 用户要求对清洗后的时间序列 xlsx 文件进行可视化，生成折线图。

### 工作流程

1. **确认文件**：用户指定一个清洗后的 `.xlsx` 文件，应包含时间变量和数值变量
2. **判断数据频率**：根据清洗后 xlsx 的列结构判断
   - **日度数据**（含 年份、季度、月份、日 四列）→ `ymd()` + `tsset,d` + `tsline`
   - **月度数据**（含 年份、季度、月份 三列，无日列）→ `ym()` + `tsset,m` + `tsline`
   - **季度数据**（含 年份、季度 两列，无月份列）→ `yq()` + `tsset,q` + `tsline`
   - **年度数据**（仅含 年份 一列）→ 数值÷10 + `twoway connected`
3. **生成 .do 文件**，写入 Stata do 脚本

**日度数据模板**（如 iCPI）：
```stata
clear
cd "E:\AI\test"
import excel "<文件名>.xlsx",firstrow
gen date = mdy(月份, 日, 年份)
tsset date,d
tsline <数值变量>,xtitle("时间")
graph export <文件名>.png ,width(3500) height(2500) replace
```

**月度数据模板**（如 CPI）：
```stata
clear
cd "E:\AI\test"
import excel "<文件名>.xlsx",firstrow
gen date = ym(年份,月份)
tsset date,m
tsline <数值变量>,xtitle("时间")
graph export <文件名>.png ,width(3500) height(2500) replace
```

**季度数据模板**（如季度GDP）：
```stata
clear
cd "E:\AI\test"
import excel "<文件名>.xlsx",firstrow
gen date = yq(年份,季度)
tsset date,q
tsline <数值变量>,xtitle("时间")
graph export <文件名>.png ,width(3500) height(2500) replace
```

**年度数据模板**（如武汉GDP）：
```stata
clear
cd "E:\AI\test"
import excel "<文件名>.xlsx",firstrow
gen <数值变量>_十亿 = <数值变量> / 10
twoway connected <数值变量>_十亿 年份, ///
  title("<标题>") ///
  ytitle("<纵轴标签>") xtitle("年份") ///
  scheme(s2color)
graph export <文件名>.png ,width(3500) height(2500) replace
```

4. **执行 Stata 批处理**：
   ```powershell
   Start-Process -FilePath "<STATA_EXE_PATH>" `
     -ArgumentList "/e do `"<path/to/file.do>`"" `
     -WorkingDirectory "<STATA_DIR>" -Wait
   ```
5. **输出结果**：PNG 图片保存在工作空间，文件名为原 xlsx 文件名 + `.png`

### 注意事项

- ⚠️ 使用前请将 `<STATA_EXE_PATH>` 和 `<STATA_DIR>` 替换为你的 Stata 实际路径
- 不修改 Stata 默认配色（不使用 `mcolor`/`lcolor` 选项）
- 不添加 `exit, clear` 以外的多余命令
- 年度数据默认数值单位为亿元，自动转换为十亿元
- 日度用 `mdy(月份,日,年份)` + `tsset,d`，月度用 `ym(年份,月份)` + `tsset,m`，季度用 `yq(年份,季度)` + `tsset,q`
- 图片路径记得让用户通过 `deliver_attachments` 获取

---

| 用户意图 | 触发 Mode |
|----------|-----------|
| "帮我运行" / "执行" / "run" / "跑一下" | **Mode A** |
| "帮我解释" / "逐行分析" / "看看这段代码" / "不运行" / "这是什么意思" | **Mode B** |
| "帮我清洗" / "时间序列" / "提取季度" / "删除非样本" / "清洗数据" / 涉及原始Excel时间数据的整理 | **Mode C** |
| "可视化" / "画图" / "折线图" / "绘图" / "趋势图" / 涉及清洗后xlsx的画图 | **Mode D** |
| 只提供代码，未明确说明 | 询问用户："请问需要**运行**这段代码，还是只需要**解释**？还是需要**清洗**时间序列数据？还是需要**可视化**？" |

---

## Example Interaction Patterns

**Pattern 1 — 运行对话框代码（Mode A）:**
> "帮我运行: import numpy as np; print(np.random.randn(5))"

→ 写入临时 `.py` 文件，执行，报告输出结果。

**Pattern 2 — 运行现有 .py 文件（Mode A）:**
> "运行工作空间里的 analysis.py"

→ 定位文件，执行，报告输出与错误。

**Pattern 3 — 图形输出（Mode A）:**
> "运行这段 matplotlib 绘图代码，并保存为 PNG"

→ 在代码末尾自动添加 `plt.savefig("E:\\AI\\test\\output.png", dpi=150, bbox_inches='tight')`，执行，报告图片路径。

**Pattern 4 — 解析代码（Mode B）:**
> "帮我解释这段 Python 代码，不需要运行"

→ 静态分析代码，输出逐块解释 + 总结评价，**不执行任何命令**。

**Pattern 5 — 解析 .py 文件（Mode B）:**
> "帮我看看 heart.py 写的是什么"

→ 读取文件内容，输出逐块解释 + 总结评价，**不执行任何命令**。

**Pattern 6 — 缺少依赖（Mode A 异常处理）:**
> 运行后出现 `ModuleNotFoundError: No module named 'pandas'`

→ 提示：`pip install pandas`，询问是否自动安装并重试。

**Pattern 7 — 时间序列数据清洗（Mode C）:**
> "帮我清洗国内生产总值.xlsx，提取季度信息"

→ 先用 `--probe` 探查文件结构，确认时间列和数值列。确认数据频率后加上 `--frequency quarterly`（季度）或 `--frequency daily`（日度），然后执行 `ts_clean.py` 清洗脚本，最后报告结果并告知输出文件路径。

**Pattern 8 — 时间序列可视化（Mode D）:**
> "请对国内生产总值湖北武汉_清洗后.xlsx进行可视化"
> "请对互联网在线数据的居民消费价格指数iCPI_清洗后进行可视化"

→ 根据清洗后 xlsx 的列结构判断频率，选择对应 Stata 模板（日度/月度/季度/年度），生成 .do 文件，运行 Stata 批处理并交付图片。
