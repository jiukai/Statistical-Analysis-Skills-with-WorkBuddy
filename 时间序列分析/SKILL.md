---
name: 时间序列分析
description: >
  This skill should be used when the user wants to clean raw time-series data
  from Excel files, or visualize cleaned time-series data.
  It removes non-sample rows (metadata, statistics, empty rows), converts date
  formats, extracts time components (year/month/quarter/day), and exports clean
  results as xlsx with a cleaning log.
  It also generates line charts from cleaned time-series xlsx files using Stata,
  producing png output with proper frequency-aware date handling.
---

# 时间序列分析 Skill

时间序列数据清洗 + 可视化一站式工具。

---

## When to Use

Load this skill when the user:
- Asks to **clean** raw time-series data (e.g., Excel files with daily/monthly/quarterly/yearly dates)
- Asks to **filter out non-sample rows** from CEIC/Wind/Economist-style datasets
- Uses phrases like "清洗数据", "时间序列", "提取季度", "删除非样本行"
- Asks to **visualize** a cleaned time-series xlsx, generate a line chart
- Uses phrases like "可视化", "画图", "折线图", "绘图", "趋势图"

---

## 配套脚本

清洗脚本位于本技能目录 `scripts/ts_clean.py`。

可视化通过 Stata 批处理完成，Stata 路径需根据实际情况配置。

---

## Mode A — 时间序列数据清洗

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
6. **小数精度**：是否指定小数位数。默认自动检测——当一半以上数值有 n 位小数时，全部统一为 n 位

### Step 2 — 探查数据

用 `--probe` 快速探查文件结构：

```bash
python scripts/ts_clean.py --input "<file.xlsx>" --probe
```

探查结果包含：总行数、出现的列、首个有数据行、最后一个有数据行。

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

**月度数据示例：**
```bash
python scripts/ts_clean.py \
  --input "<file.xlsx>" \
  --time-col "A" \
  --value-cols "B" \
  --value-names "居民消费价格指数" \
  --frequency monthly
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

**年度数据示例：**
```bash
python scripts/ts_clean.py \
  --input "<file.xlsx>" \
  --time-col "A" \
  --value-cols "B" \
  --value-names "国内生产总值" \
  --frequency yearly
```

参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | (必填) | 原始 xlsx 文件路径 |
| `--time-col` | `A` | 时间变量所在列字母 |
| `--value-cols` | `B` | 数值变量列字母列表，逗号分隔（如 "B,C,D"） |
| `--value-names` | `列X` | 数值变量名称列表，逗号分隔 |
| `--time-format` | `auto` | 时间格式：`serial`(Excel序列号)、`string`(日期文本)、`auto`(自动检测) |
| `--frequency` | `daily` | 数据频率：`daily` / `monthly` / `quarterly` / `yearly` |
| `--decimal-places` | 自动 | 小数保留位数。不指定时自动检测 |
| `--output-xlsx` | 自动生成 | 清洗后 xlsx 输出路径 |
| `--output-txt` | 自动生成 | 清洗流程说明输出路径 |
| `--probe` | - | 仅探查文件，不执行清洗 |

### Step 4 — 分析并报告

| 项目 | 说明 |
|------|------|
| **原始规模** | 原始 xlsx 总行数（含空行） |
| **非样本行** | 自动识别的统计信息/元数据/空行数量 |
| **有效观测** | 保留的样本观测值数量 |
| **数据频率** | 用户指定的频率 |
| **时间范围** | 清洗后的数据覆盖的时间范围 |
| **时间格式** | 检测到的时间格式类型 |
| **转换错误** | 时间变量转换失败的行数 |
| **输出变量** | 输出的变量列表（按频率自动生成） |
| **输出文件** | 清洗后的 xlsx 和清洗流程文档路径 |

### 非样本行自动识别规则

1. **全空行** → 非样本
2. **首列时间变量为空，但其他列有值** → 非样本（典型统计信息行）
3. **首列时间变量和数值列均有值** → 样本行（予以保留）

### 小数精度统一规则

自动检测原始数据中数值的小数位数：
1. 扫描所有数值列原始值（跳过整数）
2. 统计各小数位数出现频次
3. 若某一位数占比超过 50%，全表统一到该位数
4. 无超半数情况则取出现最多的位数

可通过 `--decimal-places N` 手动指定位数。

### 错误处理

| 错误特征 | 可能原因 | 处理建议 |
|----------|----------|----------|
| `File not found` | 路径错误 | 检查文件路径拼写 |
| `No sheet1.xml` | 不是标准 xlsx | 确认文件格式 |
| 0 行保留 | 列名设置错误 | 重新确认 time-col/value-cols |
| 时间转换全部失败 | 格式不匹配 | 指定 `--time-format string` 或 `serial` |

---

## Mode B — 时间序列可视化

> **触发条件**: 用户要求对清洗后的时间序列 xlsx 文件进行可视化，生成折线图。

### 工作流程

1. **确认文件**：用户指定一个清洗后的 `.xlsx` 文件，应包含时间变量和数值变量
2. **判断数据频率**：根据清洗后 xlsx 的列结构判断
   - **日度数据**（含 年份、季度、月份、日 四列）→ `ymd()` + `tsset,d` + `tsline`
   - **月度数据**（含 年份、季度、月份 三列，无日列）→ `ym()` + `tsset,m` + `tsline`
   - **季度数据**（含 年份、季度 两列，无月份列）→ `yq()` + `tsset,q` + `tsline`
   - **年度数据**（仅含 年份 一列）→ 数值÷10 + `twoway connected`
3. **生成 .do 文件**，写入 Stata do 脚本
4. **执行 Stata 批处理**
5. **输出结果**：PNG 图片保存在工作空间

### 各频率 Stata 模板

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

### 执行 Stata 批处理

```powershell
Start-Process -FilePath "<STATA_EXE_PATH>" `
  -ArgumentList "/e do `"<path/to/file.do>`"" `
  -WorkingDirectory "<STATA_DIR>" -Wait
```

### 注意事项

- 不修改 Stata 默认配色（不使用 `mcolor`/`lcolor` 选项）
- 不添加 `exit, clear` 以外的多余命令
- 年度数据默认数值单位为亿元，自动转换为十亿元
- 图片路径通过 `deliver_attachments` 交付给用户

---

## Mode C — 时间序列分析报告

> **触发条件**: 用户要求对一份或多份时间序列数据进行分析并出具分析报告。涉及短语如"分析报告"、"数据分析"、"撰写报告"、"分析一下"。

### 三阶段流程

调用此功能时严格按如下顺序执行三个阶段，不可跳过或合并：

#### 阶段一：清洗所有原始数据文件

对用户指定的**每一份**原始 xlsx 文件依次执行 Mode A — 时间序列清洗：

1. 确定每个文件的：时间列、数值列、频率、小数精度
2. 用 `ts_clean.py` 执行清洗，生成 `*_清洗后.xlsx` 和 `*_清洗流程.txt`
3. 记录每个文件的：有效观测数、时间范围、变量名、关键统计量

> 如果某个文件已经存在对应的 `*_清洗后.xlsx`，可跳过清洗阶段，直接使用已有结果。

#### 阶段二：可视化所有清洗后文件

对**每一份**已清洗的 xlsx 文件依次执行 Mode B — 时间序列可视化：

1. 根据文件列结构判断频率
2. 写入 .do 文件并执行 Stata 批处理
3. 生成 PNG 图片

#### 阶段三：联网搜索 + 撰写分析报告

基于前面两步的结果（清洗数据和统计信息、PNG 图片），通过**联网搜索**搜集相关资料，然后以**段落形式**撰写分析报告。

##### 多文件分析策略

根据用户提供的文件数量和类型，灵活选择分析角度：

**情况一：单个文件** → 按标准三段式结构出具单一指标分析报告。

**情况二：多个文件，不同指标**（如同时提供 CPI 和 GDP）→ 分析报告应从**物价**和**产出**等多个维度综合分析中国宏观经济运行情况，探讨各指标之间的关联与相互影响，而非孤立地描述每个指标。例如，CPI 与 GDP 的关系（菲利普斯曲线）、通胀与增长的阶段特征等。

**情况三：多个文件，同一指标不同地区**（如同时提供武汉和长沙的 GDP）→ 分析报告应对两地的经济发展情况进行**对比分析**，包括经济总量差距、增长模式差异、地方政府发展战略比较、产业结构异同等，并在结论中提出针对性的发展建议。

多个文件时，所有数据系列统一放入同一份报告中，不拆分成多份独立报告。

##### 联网搜索要求

以下内容**必须**通过联网搜索获取，不得凭模型内部知识作答：
- 数据地区的经济发展概况、产业结构
- 相关领域的政府政策文件名称、发布时间和要点
- 官方发布的未来发展规划（"十四五"规划、专项规划等）
- 重大经济事件的时间点和影响
- 学术研究或权威媒体报道中的分析观点

搜索关键词建议：
- `{地区名} {指标名} 发展现状`
- `{地区名} {指标名} 政策`
- `{地区名} {指标名} 十四五规划`
- `{指标名} 趋势 影响因素`

##### 报告结构

报告以四个一级标题组成：**引言**、**数据分析**、**结论与展望**、**参考出处**。全文使用**段落形式**（不列要点、不加序号），正文中不得出现"根据搜索结果"、"据媒体报道"等类似表述。

**一、引言**
- 介绍数据所对应地区在该指标所反映领域的发展情况
- 当前发展阶段和历史背景
- 相关的政府政策文件
- 官方未来发展规划和目标
- 如果是多地区比较，引言中需分别介绍各地区的相关情况

**二、数据分析**
- 插入第二步生成的 PNG 图片
- 对图中变量的整体走势进行文字描述
- 分不同时间阶段，分析该阶段变量走势对应的现实经济情况或政府政策
- 每个阶段的转折点应提供对应的政策名称或经济事件
- 如果是多指标综合分析，需阐述指标间的联动关系
- 如果是多地区对比分析，需对比各地区走势差异并分析原因

**三、结论与展望**
- 总结数据分析的主要发现
- 对该变量未来趋势进行展望
- 提出政府引导该变量发展的政策建议
- 如果是多地区对比，需分别给出针对性的建议

**四、参考出处**
- 集中列出正文中所有引用的来源
- 正文中引用的地方在括号后加中括号和数字序号，如（来源名称，年份）[1]
- 参考出处部分以"[数字序号]"开头，后接报道标题与网址，或论文标题与期刊年份
- 格式示例：
  [1] 长沙与武汉之间的经济发展差距，就如同湘江与长江之间的... https://www.sohu.com/a/884599120_121125734
  [2] 武汉市国民经济和社会发展第十四个五年规划和2035年远景目标纲要 https://fgw.wuhan.gov.cn/...
  [3] 湖北省2025年国民经济和社会发展统计公报 https://tjj.hunan.gov.cn/...

##### 写作约束

- **不得使用要点形式**（参考出处除外），正文用连贯段落书写
- **回答时直接以报告标题开头**，不得输出任何非报告正文的内容（如"好的"、"以下是为您生成的分析报告"等开场白）
- **正文中不得出现"根据搜索结果"、"据媒体报道"、"搜索发现"等类似表述**，直接陈述事实，来源标注放在括号内
- **严禁AI幻觉**：论点、数据、结论必须严格忠于联网搜索到的官方资料和清洗/可视化结果
- **严禁"合理推断"**：不得进行任何没有搜索材料支撑的推论或结论延伸
- 凡涉及政策文件、经济数据、事件时间点，必须注明出处
- 如某些信息搜索不到，坦诚说明"未找到相关资料"，不得编造
- 如果报告以 Word/PDF 等文件形式输出，参考出处同样需包含在文件末尾

---

## 判断逻辑

| 用户意图 | 触发 Mode |
|----------|-----------|
| "帮我清洗" / "时间序列" / "提取季度" / "删除非样本" / "清洗数据" / 涉及原始Excel时间数据的整理 | **Mode A** |
| "可视化" / "画图" / "折线图" / "绘图" / "趋势图" / 涉及清洗后xlsx的画图 | **Mode B** |
| "分析报告" / "数据分析" / "撰写报告" / "分析一下" / 涉及对时间序列数据的解读和报告输出 | **Mode C** |
| 只提到文件，未明确说明 | 询问用户：请问需要**清洗**、**可视化**还是**分析报告**？ |
