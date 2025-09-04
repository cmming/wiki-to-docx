# Wiki to DOCX Converter

A collection of Python tools to convert GitHub Wiki repositories and web pages to DOCX format using pandoc.

## 工具说明 (Tools Overview)

This repository provides two main conversion tools:

### 1. `convert_wiki_to_docx.py` - GitHub Wiki to DOCX Converter

Convert GitHub Wiki repositories to a single DOCX document with proper ordering and table of contents.

**支持的输入格式 (Supported Input Formats):**
- GitHub Wiki Git repositories (`.wiki.git` URLs)
- GitHub repository URLs (automatically converts to wiki)
- GitHub Wiki page URLs 
- Local paths to wiki repositories
- 支持中文路径和页面名称 (Supports Chinese paths and page names)

### 2. `convert_url_to_docx.py` - Web Page to DOCX Converter

Convert any web page to DOCX format with smart content extraction and resource handling.

**Features:**
- Automatic content extraction using readability algorithms
- CSS selector support for precise content targeting
- Absolute URL conversion for embedded resources
- Chinese encoding support

## 安装要求 (Requirements)

### Prerequisites
- Python 3.7+
- [Pandoc](https://pandoc.org/installing.html) - Required for DOCX conversion

### Python Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests beautifulsoup4 lxml readability-lxml
```

## 使用方法 (Usage)

### GitHub Wiki to DOCX

```bash
# Convert GitHub wiki repository
python convert_wiki_to_docx.py --repo https://github.com/user/repo.wiki.git --output my-wiki.docx

# Convert from GitHub repository URL (auto-detects wiki)
python convert_wiki_to_docx.py --repo https://github.com/user/repo --output my-wiki.docx

# Convert local wiki directory
python convert_wiki_to_docx.py --repo /path/to/local/wiki --output my-wiki.docx

# With custom styling and deeper TOC
python convert_wiki_to_docx.py --repo https://github.com/user/repo.wiki.git \
    --output styled-wiki.docx \
    --reference-docx template.docx \
    --toc-depth 4
```

### Web Page to DOCX

```bash
# Convert web page with default settings
python convert_url_to_docx.py --url https://example.com/article --output article.docx

# With table of contents and custom styling
python convert_url_to_docx.py --url https://example.com/article \
    --output article.docx \
    --toc \
    --reference-docx template.docx

# Extract specific content using CSS selector
python convert_url_to_docx.py --url https://example.com/article \
    --css-selector "article.main-content" \
    --output article.docx
```

## 命令行选项 (Command Line Options)

### Wiki Converter Options
- `--repo`: Wiki repository URL or local path (required)
- `--output, -o`: Output DOCX filename (default: wiki.docx)
- `--reference-docx`: Custom DOCX template for styling
- `--toc-depth`: Table of contents depth (default: 3)
- `--keep-clone`: Keep temporary cloned directory

### URL Converter Options  
- `--url`: Web page URL to convert (required)
- `--output, -o`: Output DOCX filename (default: page.docx)
- `--toc`: Include table of contents
- `--toc-depth`: Table of contents depth (default: 3)
- `--css-selector`: CSS selector for content extraction
- `--no-readability`: Disable readability-based content extraction
- `--reference-docx`: Custom DOCX template for styling
- `--user-agent`: Custom User-Agent string
- `--timeout`: Request timeout in seconds (default: 30)

## 特性 (Features)

- **智能内容排序**: Wiki pages ordered by sidebar, with Home.md first
- **中文支持**: Full support for Chinese characters in URLs and filenames  
- **资源处理**: Automatic handling of images and links in converted documents
- **样式模板**: Support for custom DOCX styling via reference documents
- **目录生成**: Automatic table of contents generation
- **编码处理**: Robust handling of various text encodings

## License

This project is open source. Please check the repository for license details.