#!/usr/bin/env python3
"""Replace an operator's home-directory prefix in raw run logs, and change nothing else.

This is how logs/logs_paper2_rerun_2026-10_anon.tgz was produced from the operator's raw
archive (the prefix appeared 119 times; see the paper, Appendix F).

Usage:
  python3 -I anonymize_logs.py <src_dir> <dst_dir> --prefix /home/<operator>/ [--replacement /home/user/]
"""
import argparse
import os
import sys

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("dst")
ap.add_argument("--prefix", required=True, help="home-directory prefix to replace, e.g. /home/alice/")
ap.add_argument("--replacement", default="/home/user/")
a = ap.parse_args()

os.makedirs(a.dst, exist_ok=True)
total = 0
for name in sorted(os.listdir(a.src)):
    path = os.path.join(a.src, name)
    if not os.path.isfile(path):
        continue
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        data = f.read()
    n = data.count(a.prefix)
    total += n
    with open(os.path.join(a.dst, name), "w", encoding="utf-8", errors="surrogateescape") as f:
        f.write(data.replace(a.prefix, a.replacement))
    print(f"{name}: {n}")
print(f"total replacements: {total}", file=sys.stderr)
