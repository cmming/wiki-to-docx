#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WIKI_SPECIALS = {"_Sidebar.md", "_Footer.md", "_Header.md", "README.md"}

LINK_PATTERNS = [
    re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),   # [text](link)
    re.compile(r"\[\[([^\]]+)\]\]"),          # [[Wiki Style]]
]

def run(cmd, cwd=None):
    print(f"+ {' '.join(cmd)}", flush=True)
    subprocess.check_call(cmd, cwd=cwd)

def parse_args():
    p = argparse.ArgumentParser(description="Convert a GitHub Wiki repo to a single DOCX via pandoc.")
    p.add_argument("--repo", required=True, help="Git URL or local path to the wiki repo (e.g. https://github.com/owner/repo.wiki.git)")
    p.add_argument("--output", "-o", default="wiki.docx", help="Output DOCX filename (default: wiki.docx)")
    p.add_argument("--reference-docx", help="Optional reference .docx for styling (pandoc --reference-doc)")
    p.add_argument("--toc-depth", type=int, default=3, help="TOC depth (default: 3)")
    p.add_argument("--keep-clone", action="store_true", help="Keep temp clone directory if cloning from URL")
    return p.parse_args()

def is_git_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://") or s.endswith(".git")

def clone_repo(repo_url: str) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="wiki-clone-"))
    run(["git", "clone", "--depth", "1", repo_url, str(tmpdir)])
    return tmpdir

def normalize_md_stem(name: str):
    base = name.strip().strip("/")
    base = base.split("#", 1)[0]
    if base.lower().endswith(".md"):
        base = base[:-3]
    candidates = [base, base.replace(" ", "-"), base.replace(" ", "_")]
    candidates += [base.replace("%20", " "), base.replace("%20", "-"), base.replace("%20", "_")]
    seen = set()
    result = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result[0], result

def find_md_by_link(working_dir: Path, link_target: str):
    _, stems = normalize_md_stem(link_target)
    candidates = []
    for stem in stems:
        candidates.append(working_dir / f"{stem}.md")
        candidates.append(working_dir / stem / "Home.md")
        candidates.append(working_dir / stem)
    for c in candidates:
        if c.exists() and c.is_file() and c.suffix.lower() == ".md":
            return c
    return None

def parse_sidebar_order(working_dir: Path):
    sidebar = working_dir / "_Sidebar.md"
    order = []
    if not sidebar.exists():
        return order
    text = sidebar.read_text(encoding="utf-8", errors="ignore")
    found = []
    for pat in LINK_PATTERNS:
        for m in pat.findall(text):
            target = m[1].strip() if isinstance(m, tuple) else m.strip()
            if "://" in target:
                continue
            md = find_md_by_link(working_dir, target)
            if md:
                found.append(md)
    seen = set()
    for p in found:
        key = str(p.resolve())
        if key not in seen and p.name not in WIKI_SPECIALS:
            seen.add(key)
            order.append(p)
    return order

def collect_md_files(working_dir: Path):
    files = [p for p in working_dir.glob("*.md") if p.name not in WIKI_SPECIALS]
    result = []
    home = working_dir / "Home.md"
    if home.exists():
        result.append(home)
    sidebar_order = parse_sidebar_order(working_dir)
    for f in sidebar_order:
        if f not in result:
            result.append(f)
    remaining = [f for f in files if f not in result]
    remaining.sort(key=lambda p: p.name.lower())
    result.extend(remaining)
    return result

def ensure_tools():
    try:
        subprocess.check_output(["pandoc", "-v"])
    except Exception:
        print("错误：未检测到 pandoc。请先安装 pandoc；参考：https://pandoc.org/installing.html", file=sys.stderr)
        sys.exit(1)

def main():
    args = parse_args()
    ensure_tools()

    temp_dir = None
    try:
        if is_git_url(args.repo):
            temp_dir = clone_repo(args.repo)
            working_dir = temp_dir
        else:
            working_dir = Path(args.repo).expanduser().resolve()
            if not working_dir.exists():
                print(f"错误：路径不存在：{working_dir}", file=sys.stderr)
                sys.exit(1)

        md_files = collect_md_files(working_dir)
        if not md_files:
            print("未找到任何 Markdown 文件。", file=sys.stderr)
            sys.exit(1)

        print("将按以下顺序合并为 DOCX：")
        for i, f in enumerate(md_files, 1):
            print(f"{i:02d}. {f.name}")

        output_path = Path(args.output).expanduser().resolve()
        cmd = [
            "pandoc",
            "--from", "gfm",
            "--to", "docx",
            "--output", str(output_path),
            "--standalone",
            "--toc",
            f"--toc-depth={args.toc_depth}",
            f"--resource-path={str(working_dir)}",
        ]
        if args.reference_docx:
            cmd.extend(["--reference-doc", str(Path(args.reference_docx).expanduser().resolve())])
        cmd.extend([str(p) for p in md_files])

        run(cmd, cwd=str(working_dir))
        print(f"已生成：{output_path}")

    finally:
        if temp_dir and not args.keep_clone:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()