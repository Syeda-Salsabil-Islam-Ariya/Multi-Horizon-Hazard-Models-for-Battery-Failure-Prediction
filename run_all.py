#!/usr/bin/env python3
"""Run the full battery hazard pipeline: install deps, benchmark, figures, paper."""

import subprocess, sys, os, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(ROOT, "src")
DATA = os.path.join(ROOT, "data")

def run(cmd, cwd=SRC):
    print(f"\n{'='*60}\n$ {' '.join(cmd)}\n{'='*60}")
    subprocess.check_call(cmd, cwd=cwd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Re-run benchmark even if results exist")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install")
    args = parser.parse_args()

    if not args.skip_install:
        run([sys.executable, "-m", "pip", "install", "-r", os.path.join(ROOT, "requirements.txt")])

    results_csv = os.path.join(DATA, "benchmark_results.csv")
    if args.force or not os.path.exists(results_csv):
        run([sys.executable, "benchmark_cv.py"])
    else:
        print(f"\n[SKIP] benchmark_cv.py — {results_csv} exists (use --force to re-run)")

    run([sys.executable, "plot_fig01_fig03_fig04.py"])
    run([sys.executable, "plot_fig02.py"])
    run([sys.executable, "plot_fig05.py"])
    run([sys.executable, "generate_paper.py"])

    print(f"\n{'='*60}\nDONE. Output files:\n{'='*60}")
    for f in sorted(os.listdir(DATA)):
        if f.startswith("Fig") and f.endswith(".png"):
            print(f"  data/{f}")
    print(f"  paper/paper.docx")

if __name__ == "__main__":
    main()
