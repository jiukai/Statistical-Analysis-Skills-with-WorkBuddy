---
name: Stata-run
description: >
  This skill should be used when the user wants to run Stata commands or .do files,
  OR when the user wants to explain/parse Stata code without running it.
  It locates the Stata executable on the system, executes the provided commands or
  .do file in batch mode, captures the log output, and produces a structured analysis
  report covering commands executed, datasets loaded/saved, data dimensions, warnings,
  and errors. It also supports a "explain mode" that parses Stata code line-by-line
  (merging trivial/loop lines) and produces a structured explanation and overall
  evaluation without executing anything.
---

# Stata-run Skill

Run Stata commands / `.do` files and analyze results, **or** explain Stata code without running it.

---

## When to Use

Load this skill when the user:
- Asks to **run** one or more Stata commands (e.g., `sysuse auto`, `regress y x`)
- Asks to **execute** an existing `.do` file in the workspace
- Wants to know what happened after running Stata code (log analysis)
- Needs to save a Stata dataset to a specific path
- Asks to **explain**, **解释**, **解读**, **逐行分析** Stata commands or a `.do` file **without running**
- Uses phrases like "这段代码是什么意思", "帮我看看这个do文件", "不运行，只解释"

---

## Mode A — Run & Report（执行模式）

### Step 1 — Locate Stata

Default installation path:

```
D:\STATA\STATA14\Stata.exe
```

> If Stata is installed elsewhere, update the path in `scripts/run_stata.py` or pass `--stata "<your_path>"`.

If not found there, search for `StataMP*.lnk` shortcuts in the workspace and resolve
the target path via PowerShell:

```powershell
(New-Object -ComObject WScript.Shell).CreateShortcut("<path>.lnk").TargetPath
```

### Step 2 — Prepare the .do file

**Case A — User provides commands in chat:**

Write a temporary `.do` file (e.g., `E:\AI\test\run_stata.do`) containing:
1. Each command on its own line
2. A final `exit, clear` line

**Case B — User points to an existing `.do` file:**

Use the file as-is. If it does not already end with `exit`, note that Stata will stay open.

### Step 3 — Execute in Batch Mode

```powershell
Start-Process -FilePath "<stata_exe>" `
  -ArgumentList "/e do `"<path/to/file.do>`"" `
  -WorkingDirectory "<stata_dir>" `
  -Wait
```

Or via the bundled Python helper:

```bash
python scripts/run_stata.py --cmd "sysuse auto" "summarize" --stata "YOUR_STATA_PATH"
python scripts/run_stata.py --do "E:\AI\test\analysis.do" --stata "YOUR_STATA_PATH"
```

### Step 4 — Locate the Log File

Stata writes the log to the **same directory as the Stata executable**, named after the `.do` file:

```
<STATA_DIR>\<do_file_stem>.log  # Replace <STATA_DIR> with your Stata installation directory
```

### Step 5 — Analyze and Report

| 项目 | 说明 |
|------|------|
| **执行状态** | 是否成功（检查 `end of do-file`，有无 `r(N)` 错误码） |
| **执行命令** | 从日志中提取以 `. ` 开头的命令行 |
| **数据加载** | `sysuse` / `use` 读入的数据集名称及描述 |
| **数据保存** | `save` / `saveold` 输出的文件路径 |
| **数据规模** | 观测值数 (obs) 和变量数 (vars) |
| **警告信息** | `(note: ...)` 等提示行 |
| **错误信息** | `r(N)` 错误码及上下文 |
| **完整日志** | 原始日志内容 |

### Key Conventions

- Always add `replace` option when saving: `save "path.dta", replace`
- Stata 14 `.dta` format is version 118; use `saveold` for backward compatibility if needed
- The log file is regenerated on each batch run — read it **after** `-Wait` returns
- Temp `.do` files can be deleted after successful execution unless the user asks to keep them
- Stata batch mode (`/e`) suppresses the GUI; no window will appear

### Error Handling

| 错误特征 | 可能原因 | 处理建议 |
|----------|----------|----------|
| `r(601)` | 路径错误或文件不存在 | 检查路径拼写 |
| `r(111)` | 变量名或命令拼写错误 | 检查大小写 |
| `r(198)` | 命令语法错误 | 参考 `help <command>` |
| Log file empty | Stata 未启动或路径问题 | 确认 Stata.exe 路径正确 |
| `end of do-file` missing | 中途崩溃或未 `exit` | 检查错误码 |

---

## Mode B — Explain（代码解析模式）

> **触发条件**: 用户明确表示"不运行/只解释/帮我看看/这是什么意思"，或提供代码但未要求执行时。

**不执行任何命令**，仅对代码进行静态分析和解释。

### 解析规则

1. **逐段解释**：将代码按逻辑分块（数据准备、变量生成、统计分析、图形绘制、导出等），每块给出统一解释，而非机械地每行一条。
2. **合并处理以下情形**：
   - 循环体（`foreach` / `forvalues` / `while`）：整体解释循环逻辑，不逐行展开
   - 连续的 `gen`/`replace` 语句且目的相同：合并为一条说明
   - 连续的 `gr_edit` / 图形编辑命令：合并为"图形美化/标注"一条
   - 连续的 `label`、`rename`、`drop`、`keep` 等整理命令：合并说明
3. **注释行**（`//` 或 `*` 开头）：与紧随其后的代码块合并解释，说明注释意图是否与代码一致。
4. **命令格式统一**：每个解释块输出为表格或列表，包含：
   - 代码片段（原始，可多行）
   - 功能说明（用中文，简洁）
   - 关键参数说明（若有选项如 `lc()`, `lw()`, `replace` 等，逐一说明含义）

### 输出格式

输出分两部分：

#### 第一部分：逐块解释

```
### [序号] [功能概括标题]

**代码：**
\```stata
<原始代码块>
\```

**解释：**
<功能描述，1-3句话>

**关键参数：**
- `参数名`: 说明
```

对于简单命令，可以省略"关键参数"小节。

#### 第二部分：总结评价

输出以下内容：

| 评价维度 | 内容 |
|----------|------|
| **代码目的** | 用1-2句话概括整段代码的总体目标 |
| **数据流向** | 数据从哪里来 → 经过哪些变换 → 输出到哪里 |
| **技术亮点** | 值得学习或巧妙的写法（如有） |
| **潜在问题** | 可能出错的地方、兼容性风险、编码风险等（如有） |
| **改进建议** | 可选，如有更简洁/健壮的写法可提出 |

### 解析示例

**用户输入：**
> 帮我解释这段代码（不需要运行）：
> ```stata
> sysuse auto
> gen price_log = log(price)
> regress price_log mpg weight
> ```

**输出示例：**

---

### [1] 加载内置数据集

**代码：**
```stata
sysuse auto
```
**解释：**
加载 Stata 自带的 1978 年汽车数据集（74 条观测值），包含价格、里程、重量等变量。

---

### [2] 生成对数价格变量

**代码：**
```stata
gen price_log = log(price)
```
**解释：**
对 `price` 变量取自然对数，生成新变量 `price_log`，常用于处理右偏分布、满足线性回归的正态性假设。

---

### [3] 线性回归

**代码：**
```stata
regress price_log mpg weight
```
**解释：**
以 `price_log` 为因变量，`mpg`（每加仑英里数）和 `weight`（车重）为自变量进行 OLS 回归。

---

#### 总结评价

| 评价维度 | 内容 |
|----------|------|
| **代码目的** | 探究汽车价格（取对数）与燃油效率、车重的线性关系 |
| **数据流向** | 内置数据集 → 对数变换 → OLS 回归 |
| **技术亮点** | 对价格取对数是标准做法，有助于改善残差正态性 |
| **潜在问题** | 未检查 `price` 是否含零或负值（取对数前应验证） |
| **改进建议** | 可加 `vce(robust)` 使用异方差稳健标准误 |

---

## Mode 判断逻辑

| 用户意图 | 触发 Mode |
|----------|-----------|
| "帮我运行" / "执行" / "run" | **Mode A** |
| "帮我解释" / "逐行分析" / "看看这段代码" / "不运行" / "这是什么意思" | **Mode B** |
| 只提供代码，未明确说明 | 询问用户："请问需要**运行**这段代码，还是只需要**解释**？" |

---

## Example Interaction Patterns

**Pattern 1 — 运行对话框命令（Mode A）:**
> "帮我运行: sysuse nlsw88, then tabulate race"

→ Write `.do`, run batch, analyze log, report results.

**Pattern 2 — 运行现有 .do 文件（Mode A）:**
> "运行工作空间里的 analysis.do"

→ Locate file, run batch, analyze log, report results.

**Pattern 3 — 保存数据（Mode A）:**
> "加载 auto 数据集并保存为 JK.dta"

→ Write `.do` with `sysuse auto` + `save "...\JK.dta", replace`, run, report.

**Pattern 4 — 解析代码（Mode B）:**
> "帮我解释这段 Stata 代码，不需要运行"

→ 静态分析代码，输出逐块解释 + 总结评价，**不启动 Stata**。

**Pattern 5 — 解析 .do 文件（Mode B）:**
> "帮我看看 heart.do 写的是什么"

→ 读取文件内容，输出逐块解释 + 总结评价，**不启动 Stata**。
