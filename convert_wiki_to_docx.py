#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

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
    p.add_argument("--repo", required=True, help="支持以下形式：.wiki.git、仓库 URL、Wiki 页面 URL、或本地路径")
    p.add_argument("--output", "-o", default="wiki.docx", help="输出 DOCX 文件名 (default: wiki.docx)")
    p.add_argument("--reference-docx", help="可选：自定义样式 .docx（传给 pandoc --reference-doc）")
    p.add_argument("--toc-depth", type=int, default=3, help="目录深度 (default: 3)")
    p.add_argument("--keep-clone", action="store_true", help="若从远程克隆：保留临时目录")
    return p.parse_args()

def is_remote(s: str) -> bool:
    s = s.strip()
    return s.startswith(("http://", "https://", "git@"))

def to_wiki_git_remote(s: str) -> str:
    """
    将常见的 GitHub 仓库 URL 或 Wiki 页面 URL 规范化为 .wiki.git 远程地址。
    同时兼容已是 .wiki.git 的情形；兼容 git@ 形式。
    """
    s = s.strip()

    # 已是 .wiki.git
    if s.endswith(".wiki.git"):
        return s

    # git@ 形式：git@host:owner/repo(.git|.wiki.git)?
    if s.startswith("git@"):
        m = re.match(r"^git@([^:]+):([^/]+)/(.+?)(?:\.git|\.wiki\.git)?$", s)
        if m:
            host, owner, repo = m.groups()
            if repo.endswith(".wiki"):
                repo = repo[:-5]
            return f"git@{host}:{owner}/{repo}.wiki.git"
        return s

    # http(s) 形式：处理 github.com/{owner}/{repo} 或 github.com/{owner}/{repo}/wiki/...
    if s.startswith(("http://", "https://")):
        u = urlparse(s)
        path = u.path.strip("/")
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            # 去掉可能的 .git 或 .wiki 后缀
            if repo.endswith(".git"):
                repo = repo[:-4]
            if repo.endswith(".wiki"):
                repo = repo[:-5]
            return f"{u.scheme}://{u.netloc}/{owner}/{repo}.wiki.git"

    # 其他情况：原样返回（可能是本地路径或不可识别的远程）
    return s

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
        repo_input = args.repo.strip()

        # 本地路径优先
        local_path = Path(repo_input).expanduser()
        if local_path.exists() and local_path.is_dir():
            working_dir = local_path.resolve()
        else:
            # 远程：将 URL/ssh 统一转换为 .wiki.git
            if is_remote(repo_input):
                remote = to_wiki_git_remote(repo_input)
                print(f"解析远程地址：{repo_input} -> {remote}")
                temp_dir = clone_repo(remote)
                working_dir = temp_dir
            else:
                print(f"错误：无法识别的输入（既不是本地路径，也不是 URL/SSH 地址）：{repo_input}", file=sys.stderr)
                sys.exit(1)

        md_files = collect_md_files(working_dir)
        if not md_files:
            print("未找到任何 Markdown 文件。", file=sys.stderr)
            sys.exit(1)

        print("将按以下序列合并为 DOCX：")
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