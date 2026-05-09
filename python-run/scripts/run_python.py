#!/usr/bin/env python3
"""
run_python.py  —  Python-run skill helper script
================================================
Executes a Python script file or inline code, captures stdout/stderr,
and returns a structured execution report.

Usage:
  python run_python.py --file <path/to/script.py>
  python run_python.py --code "print('hello')" "x = 1+1" "print(x)"
  python run_python.py --file <path> --python <python_executable>
  python run_python.py --file <path> --timeout 30
"""

import argparse
import subprocess
import sys
import os
import tempfile
import time
import pathlib


def find_python() -> str:
    """Locate a usable Python interpreter."""
    candidates = [sys.executable, "python", "python3", "py"]
    for c in candidates:
        try:
            result = subprocess.run(
                [c, "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return c
        except Exception:
            continue
    return sys.executable  # fallback


def run_script(script_path: str, python_exe: str, timeout: int) -> dict:
    """Execute a .py file and return a result dict."""
    start = time.time()
    try:
        result = subprocess.run(
            [python_exe, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed = time.time() - start
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed": round(elapsed, 3),
            "script_path": script_path,
            "python_exe": python_exe,
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"[TimeoutExpired] Script exceeded {timeout}s limit.",
            "elapsed": round(elapsed, 3),
            "script_path": script_path,
            "python_exe": python_exe,
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -2,
            "stdout": "",
            "stderr": str(e),
            "elapsed": 0,
            "script_path": script_path,
            "python_exe": python_exe,
        }


def print_report(res: dict):
    """Print a human-readable execution report."""
    status = "✅ 成功" if res["success"] else "❌ 失败"
    print("=" * 60)
    print(f"执行状态  : {status}  (returncode={res['returncode']})")
    print(f"脚本路径  : {res['script_path']}")
    print(f"解释器    : {res['python_exe']}")
    print(f"耗时      : {res['elapsed']}s")
    print("-" * 60)
    if res["stdout"]:
        print("【标准输出】")
        print(res["stdout"])
    else:
        print("【标准输出】（无）")
    if res["stderr"]:
        print("【标准错误/警告】")
        print(res["stderr"])
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Python-run skill helper")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to a .py file to execute")
    group.add_argument("--code", nargs="+", help="Inline code lines to execute")
    parser.add_argument("--python", default=None, help="Python executable path")
    parser.add_argument("--timeout", type=int, default=60, help="Execution timeout in seconds")
    parser.add_argument("--keep", action="store_true", help="Keep temp .py file after execution")
    args = parser.parse_args()

    python_exe = args.python or find_python()
    tmp_file = None

    if args.code:
        # Write inline code to a temp file
        code = "\n".join(args.code)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False,
            encoding="utf-8", prefix="pyrun_"
        )
        tmp.write(code)
        tmp.close()
        tmp_file = tmp.name
        script_path = tmp_file
    else:
        script_path = args.file

    res = run_script(script_path, python_exe, args.timeout)
    print_report(res)

    if tmp_file and not args.keep:
        try:
            os.unlink(tmp_file)
        except Exception:
            pass

    sys.exit(0 if res["success"] else 1)


if __name__ == "__main__":
    main()
