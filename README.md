# Statistical Analysis Skills with WorkBuddy

> 面向经管科研的统计软件AI教育智能体技能包
> AI-powered Statistical Analysis Skills for WorkBuddy Platform

## 📦 Skills Included

| Skill | Description |
|---|---|
| **Stata-run** | Run and explain Stata .do files via natural language; auto-detects Stata installation |
| **python-run** | Run and explain Python scripts; supports time series cleaning & Stata-based visualization |
| **时间序列分析** (Time Series Analysis) | Three-in-one: data cleaning → visualization → auto-generated analysis report |

## 🧭 Who Needs This

- **经济学/管理学教师**：将时间序列分析教学从"写代码"升级为"提问题"，降低学生软件操作门槛
- **本科生/研究生**：上传原始经济数据，自然语言完成清洗→画图→写报告全流程
- **科研人员**：快速处理 CEIC、Wind 等数据库导出的宏观时间序列数据
- **统计课程改革者**：探索 AI 赋能经管类实验教学的新范式

## 🚀 Installation

### Prerequisites

- [WorkBuddy](https://www.codebuddy.cn/) installed
- Python 3.10+ with `openpyxl` (`pip install openpyxl`)
- (Optional, for visualization) Stata 14+ installed

### Quick Install

```bash
# 1. Extract all 3 skill packages to your WorkBuddy skills directory
# Windows PowerShell:
Expand-Archive -Path "Stata-run.zip" -DestinationPath "$env:USERPROFILE\.workbuddy\skills\"
Expand-Archive -Path "python-run.zip" -DestinationPath "$env:USERPROFILE\.workbuddy\skills\"
Expand-Archive -Path "时间序列分析.zip" -DestinationPath "$env:USERPROFILE\.workbuddy\skills\"
```

### Configure Paths (if needed)

#### Stata Path
Edit `~/.workbuddy/skills/Stata-run/scripts/run_stata.py` and update the `STATA_SEARCH_PATHS` list to include your Stata installation path.

#### Python Path
python-run skill auto-detects Python from common locations. If needed, set it manually in the dialog.

### Verify Installation

Open WorkBuddy dialog and try:

```
@skill://Stata-run  help
@skill://python-run  help
@skill://时间序列分析  help
```

## 🎯 Usage Examples

### Stata-run
```
@skill://Stata-run  sysuse auto, clear; summarize
@skill://Stata-run  运行 analysis.do 文件
```

### python-run
```
@skill://python-run  print("Hello World")
@skill://python-run  解释这段代码
```

### 时间序列分析 (Time Series Analysis)
```
@skill://时间序列分析  清洗时间序列数据：GDP.xlsx，这是一份季度数据
@skill://时间序列分析  请对GDP_清洗后 进行可视化
@skill://时间序列分析  请对CPI.xlsx 和 GDP.xlsx 进行分析并出具报告
```

## 📁 Repository Structure

```
Statistical-Analysis-Skills-with-WorkBuddy/
├── Stata-run/
│   ├── SKILL.md
│   └── scripts/
│       └── run_stata.py
├── python-run/
│   ├── SKILL.md
│   └── scripts/
│       └── run_python.py
├── 时间序列分析/
│   ├── SKILL.md
│   └── scripts/
│       └── ts_clean.py
└── README.md
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

## 📬 Contact

Created by **Jiukai Hu** (jiukai89@163.com)  
For teaching reform and academic research purposes.
