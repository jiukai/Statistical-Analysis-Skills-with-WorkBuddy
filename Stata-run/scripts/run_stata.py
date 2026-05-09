#!/usr/bin/env python3
"""
run_stata.py — Stata-run Skill Helper Script
=============================================
Locate StataMP/Stata executable, execute a .do file in batch mode,
capture the log, and print a structured analysis report.

Usage:
    python run_stata.py --do <path/to/file.do> [--stata <path/to/Stata.exe>]
    python run_stata.py --cmd "sysuse auto" "summarize" [--stata <path/to/Stata.exe>]

Options:
    --do     Path to an existing .do file to run directly.
    --cmd    One or more Stata commands (will be written to a temp .do file).
    --stata  Explicit path to Stata.exe. If omitted, auto-discovered.
    --wd     Working directory passed to Stata (default: parent dir of .do file).
    --keep   Keep the temporary .do file after execution (default: delete).
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# ── Auto-discovery: common Stata installation paths on Windows ────────────────
# 🔧 CUSTOMIZE HERE: Add or edit paths to match your Stata installation.
#    The script searches these in order and uses the first one found.
#    You can also set the STATA_PATH environment variable.
STATA_SEARCH_PATHS = [
    r"D:\STATA\STATA14\Stata.exe",
    r"C:\Program Files\Stata14\Stata.exe",
    r"C:\Program Files\Stata15\Stata.exe",
    r"C:\Program Files\Stata16\Stata.exe",
    r"C:\Program Files\Stata17\Stata.exe",
    r"C:\Program Files\Stata18\Stata.exe",
    r"C:\Program Files (x86)\Stata14\Stata.exe",
    r"C:\Program Files (x86)\Stata15\Stata.exe",
    r"C:\Program Files (x86)\Stata16\Stata.exe",
    r"C:\Program Files (x86)\Stata17\Stata.exe",
    r"C:\Program Files (x86)\Stata18\Stata.exe",
]

def find_stata():
    """Auto-discover Stata executable from known paths."""
    for p in STATA_SEARCH_PATHS:
        if Path(p).exists():
            return p
    # Fallback: search for .lnk shortcut in current workspace
    cwd = Path.cwd()
    for lnk in cwd.glob("StataMP*.lnk"):
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(lnk))
            target = shortcut.Targetpath
            if Path(target).exists():
                return target
        except Exception:
            pass
    return None

def run_stata(stata_exe: str, do_file: str, working_dir: str = None) -> dict:
    """Run Stata in batch mode and return parsed results."""
    do_path = Path(do_file).resolve()
    wd = working_dir or str(do_path.parent)
    
    cmd = [stata_exe, "/e", "do", str(do_path)]
    
    start_time = datetime.now()
    result = subprocess.run(
        cmd,
        cwd=wd,
        capture_output=True,
        text=True,
        timeout=300,
    )
    elapsed = (datetime.now() - start_time).total_seconds()

    # Stata writes log to same directory as stata exe, named after the do file
    log_candidates = [
        Path(wd) / (do_path.stem + ".log"),
        Path(stata_exe).parent / (do_path.stem + ".log"),
    ]
    log_content = ""
    log_path = None
    for lc in log_candidates:
        if lc.exists():
            log_content = lc.read_text(encoding="utf-8", errors="replace")
            log_path = str(lc)
            break

    return {
        "returncode": result.returncode,
        "elapsed": elapsed,
        "log_content": log_content,
        "log_path": log_path,
        "stderr": result.stderr,
    }

def analyze_log(log_content: str) -> dict:
    """Parse Stata log and extract key information."""
    lines = log_content.splitlines()
    
    errors = []
    warnings = []
    commands_run = []
    datasets_loaded = []
    datasets_saved = []
    observations = None
    variables = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Commands (lines starting with .)
        if re.match(r'^\.\s+\S', line):
            cmd = re.sub(r'^\.\s+', '', line).strip()
            if cmd not in ("exit, clear", "exit"):
                commands_run.append(cmd)
        
        # Errors
        if re.search(r'r\(\d+\)', stripped) or stripped.lower().startswith("error"):
            errors.append(f"Line {i+1}: {stripped}")
        
        # Warnings (note:)
        if stripped.lower().startswith("(note:") or stripped.lower().startswith("note:"):
            warnings.append(stripped)
        
        # Dataset loaded via sysuse/use
        m = re.match(r'^\((.+)\)$', stripped)
        if m and i > 0 and re.match(r'^\.\s+(sysuse|use)\s+', lines[i-1]):
            datasets_loaded.append(m.group(1))
        
        # Dataset saved
        if re.match(r'^file .+ saved$', stripped, re.IGNORECASE):
            datasets_saved.append(stripped)
        
        # obs/vars from describe or sysuse output
        m_obs = re.search(r'(\d[\d,]*)\s+obs', stripped)
        if m_obs:
            observations = m_obs.group(1).replace(",", "")
        m_var = re.search(r'(\d+)\s+var', stripped)
        if m_var:
            variables = m_var.group(1)
    
    # Check for fatal errors
    has_error = bool(errors) or "end of do-file" not in log_content
    completed = "end of do-file" in log_content

    return {
        "completed": completed,
        "has_error": has_error,
        "errors": errors,
        "warnings": warnings,
        "commands_run": commands_run,
        "datasets_loaded": datasets_loaded,
        "datasets_saved": datasets_saved,
        "observations": observations,
        "variables": variables,
    }

def print_report(run_result: dict, analysis: dict, do_file: str):
    """Print a human-readable analysis report."""
    sep = "=" * 60
    print(f"\n{sep}")
    print("  Stata-run 执行报告")
    print(sep)
    print(f"  Do 文件  : {do_file}")
    print(f"  运行时间 : {run_result['elapsed']:.2f} 秒")
    status_icon = "✅" if analysis["completed"] and not analysis["has_error"] else "❌"
    print(f"  执行状态 : {status_icon} {'成功完成' if analysis['completed'] else '执行异常'}")
    if run_result["log_path"]:
        print(f"  日志文件 : {run_result['log_path']}")
    
    print(f"\n── 执行命令 ({len(analysis['commands_run'])} 条) ──────────────────────")
    for cmd in analysis["commands_run"]:
        print(f"  • {cmd}")
    
    if analysis["datasets_loaded"]:
        print(f"\n── 数据加载 ──────────────────────────────────────────")
        for d in analysis["datasets_loaded"]:
            print(f"  📂 {d}")
    
    if analysis["datasets_saved"]:
        print(f"\n── 数据保存 ──────────────────────────────────────────")
        for d in analysis["datasets_saved"]:
            print(f"  💾 {d}")
    
    if analysis["observations"] or analysis["variables"]:
        print(f"\n── 数据规模 ──────────────────────────────────────────")
        if analysis["observations"]:
            print(f"  观测值 (obs) : {analysis['observations']}")
        if analysis["variables"]:
            print(f"  变量数 (vars): {analysis['variables']}")
    
    if analysis["warnings"]:
        print(f"\n── 提示信息 ({len(analysis['warnings'])} 条) ──────────────────────")
        for w in analysis["warnings"]:
            print(f"  ⚠️  {w}")
    
    if analysis["errors"]:
        print(f"\n── 错误信息 ({len(analysis['errors'])} 条) ──────────────────────")
        for e in analysis["errors"]:
            print(f"  ❌ {e}")
    
    print(f"\n── 完整日志 ──────────────────────────────────────────")
    print(run_result["log_content"] or "(无日志内容)")
    print(sep + "\n")

def main():
    parser = argparse.ArgumentParser(description="Run Stata commands/do-file and report results.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--do", help="Path to .do file")
    group.add_argument("--cmd", nargs="+", help="Stata commands to run")
    parser.add_argument("--stata", help="Path to Stata.exe (auto-discovered if omitted)")
    parser.add_argument("--wd", help="Working directory for Stata")
    parser.add_argument("--keep", action="store_true", help="Keep temp .do file")
    args = parser.parse_args()

    # Locate Stata
    stata_exe = args.stata or find_stata()
    if not stata_exe or not Path(stata_exe).exists():
        print("❌ 未找到 Stata 可执行文件。请使用 --stata 参数指定路径。", file=sys.stderr)
        sys.exit(1)
    print(f"📦 使用 Stata: {stata_exe}")

    # Prepare .do file
    temp_do = None
    if args.cmd:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".do", delete=False,
            dir=args.wd or os.getcwd(), encoding="utf-8"
        )
        for cmd in args.cmd:
            tmp.write(cmd + "\n")
        tmp.write("exit, clear\n")
        tmp.close()
        do_file = tmp.name
        temp_do = do_file
    else:
        do_file = args.do

    try:
        run_result = run_stata(stata_exe, do_file, working_dir=args.wd)
        analysis = analyze_log(run_result["log_content"])
        print_report(run_result, analysis, do_file)
        sys.exit(0 if analysis["completed"] and not analysis["has_error"] else 1)
    finally:
        if temp_do and not args.keep and Path(temp_do).exists():
            os.unlink(temp_do)

if __name__ == "__main__":
    main()
