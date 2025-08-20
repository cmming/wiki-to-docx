#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import tempfile
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urljoin, unquote

import requests
from bs4 import BeautifulSoup

try:
    from readability import Document
    HAVE_READABILITY = True
except Exception:
    HAVE_READABILITY = False


def run(cmd, cwd=None):
    print("+ " + " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=cwd)


def fetch_html(url: str, user_agent: str = None, timeout: int = 30) -> tuple[str, str]:
    """
    返回 (final_url, html_text)，会跟随重定向；尽量正确处理中文编码。
    """
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WikiToDocxBot/1.0; +https://github.com/cmming/wiki-to-docx)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    # 尝试用服务器声明编码；若无则由 requests/chardet 猜测
    if not resp.encoding:
        resp.encoding = resp.apparent_encoding or "utf-8"

    html = resp.text
    final_url = resp.url  # 可能经过 301/302
    return final_url, html


def absolutize_resources(soup: BeautifulSoup, base_url: str):
    """
    将相对链接/图片等资源统一转为绝对 URL；去除 <script>。
    """
    # 删除脚本，避免干扰
    for tag in soup.find_all(["script", "noscript"]):
        tag.decompose()

    # 常见资源属性统一绝对化
    attr_map = {
        "a": ["href"],
        "img": ["src", "srcset"],
        "source": ["src", "srcset"],
        "link": ["href"],
        "video": ["src", "poster"],
        "audio": ["src"],
        "iframe": ["src"],
    }

    for tag_name, attrs in attr_map.items():
        for el in soup.find_all(tag_name):
            for attr in attrs:
                val = el.get(attr)
                if not val:
                    continue
                if attr == "srcset":
                    # 处理 srcset 多 URL
                    parts = []
                    for part in val.split(","):
                        p = part.strip().split(" ")
                        if p:
                            p[0] = urljoin(base_url, p[0])
                            parts.append(" ".join([x for x in p if x]))
                    el[attr] = ", ".join(parts)
                else:
                    el[attr] = urljoin(base_url, val)


def extract_main(html: str, base_url: str, css_selector: str | None, use_readability: bool) -> BeautifulSoup:
    """
    根据优先级提取主体内容：
    1) 指定 CSS 选择器
    2) readability（若可用且启用）
    3) 常见语义容器 main/article/#content
    4) 回退到 <body>
    """
    soup = BeautifulSoup(html, "lxml")

    # CSS 选择器优先
    if css_selector:
        el = soup.select_one(css_selector)
        if el:
            wrapper = BeautifulSoup("<html><head></head><body></body></html>", "lxml")
            wrapper.head.append(wrapper.new_tag("meta", charset="utf-8"))
            title_text = soup.title.string.strip() if soup.title and soup.title.string else base_url
            title_tag = wrapper.new_tag("title")
            title_tag.string = title_text
            wrapper.head.append(title_tag)

            # 复制选中节点内容
            fragment = BeautifulSoup(str(el), "lxml")
            wrapper.body.append(fragment)
            return wrapper

    # readability
    if use_readability and HAVE_READABILITY:
        try:
            doc = Document(html)
            title_text = doc.short_title() or (soup.title.string.strip() if soup.title and soup.title.string else base_url)
            cleaned_html = doc.summary(html_partial=True)  # 仅主体片段
            wrapper = BeautifulSoup("<html><head></head><body></body></html>", "lxml")
            wrapper.head.append(wrapper.new_tag("meta", charset="utf-8"))
            title_tag = wrapper.new_tag("title")
            title_tag.string = title_text
            wrapper.head.append(title_tag)
            fragment = BeautifulSoup(cleaned_html, "lxml")
            wrapper.body.append(fragment)
            return wrapper
        except Exception:
            # 忽略提取失败，继续后续策略
            pass

    # 常见语义容器
    for sel in ["main", "article", "#content", ".content", "#main", ".post", "#root"]:
        el = soup.select_one(sel)
        if el:
            wrapper = BeautifulSoup("<html><head></head><body></body></html>", "lxml")
            wrapper.head.append(wrapper.new_tag("meta", charset="utf-8"))
            title_text = soup.title.string.strip() if soup.title and soup.title.string else base_url
            title_tag = wrapper.new_tag("title")
            title_tag.string = title_text
            wrapper.head.append(title_tag)
            fragment = BeautifulSoup(str(el), "lxml")
            wrapper.body.append(fragment)
            return wrapper

    # 回退：全页 body
    wrapper = BeautifulSoup("<html><head></head><body></body></html>", "lxml")
    wrapper.head.append(wrapper.new_tag("meta", charset="utf-8"))
    title_text = soup.title.string.strip() if soup.title and soup.title.string else base_url
    title_tag = wrapper.new_tag("title")
    title_tag.string = title_text
    wrapper.head.append(title_tag)
    body = soup.body or soup
    fragment = BeautifulSoup(str(body), "lxml")
    wrapper.body.append(fragment)
    return wrapper


def main():
    ap = argparse.ArgumentParser(description="Convert a web page URL directly to DOCX using Pandoc.")
    ap.add_argument("--url", required=True, help="网页 URL（支持中文）")
    ap.add_argument("--output", "-o", default="page.docx", help="输出 DOCX 文件名")
    ap.add_argument("--css-selector", help="可选：CSS 选择器提取主内容（如 #content, main, article）")
    ap.add_argument("--readability", action="store_true", help="启用智能正文抽取（readability）")
    ap.add_argument("--user-agent", help="自定义 User-Agent")
    ap.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒）")
    ap.add_argument("--toc-depth", type=int, default=3, help="目录深度（需要传入 --toc 生效）")
    ap.add_argument("--toc", action="store_true", help="生成目录")
    ap.add_argument("--reference-docx", help="可选：自定义样式模板（传给 pandoc --reference-doc）")
    args = ap.parse_args()

    # 处理并解码中文 URL
    raw_url = args.url.strip()
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        print(f"错误：URL 缺少协议（例如 https://）：{raw_url}", file=sys.stderr)
        sys.exit(1)

    try:
        final_url, html = fetch_html(raw_url, user_agent=args.user_agent, timeout=args.timeout)
    except Exception as e:
        print(f"抓取失败：{e}", file=sys.stderr)
        sys.exit(1)

    # 提取主体并修正资源链接
    doc = extract_main(html, final_url, args.css_selector, args.readability)
    absolutize_resources(doc, final_url)

    # 写入临时 HTML 文件
    tmpdir = Path(tempfile.mkdtemp(prefix="url2docx-"))
    try:
        html_path = tmpdir / "page.html"
        html_path.write_text(str(doc), encoding="utf-8")

        # 组装 pandoc 命令
        cmd = [
            "pandoc",
            "--from", "html",
            "--to", "docx",
            "--standalone",
            "--output", str(Path(args.output).expanduser().resolve()),
        ]
        if args.toc:
            cmd.extend(["--toc", f"--toc-depth={args.toc_depth}"])
        if args.reference_docx:
            cmd.extend(["--reference-doc", str(Path(args.reference_docx).expanduser().resolve())])

        # 注意：对于 DOCX，pandoc 会将图片等资源打包进文档。我们已经将相对 URL 变为绝对 URL。
        cmd.append(str(html_path))

        run(cmd)
        print(f"已生成：{Path(args.output).resolve()}")
    finally:
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()