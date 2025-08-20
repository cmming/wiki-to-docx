# Wiki to DOCX via GitHub Actions

This repository contains a workflow that clones a GitHub Wiki (the `.wiki.git` repo), merges Markdown pages (respecting `_Sidebar.md` order when present), and produces a single DOCX with a TOC via Pandoc.

## How to run

1. Go to the Actions tab, select "Build DOCX from GitHub Wiki".
2. Click "Run workflow".
3. Keep the default wiki URL `https://github.com/coze-dev/coze-studio.wiki.git` or change it, set an output name if you like, then run.
4. After it finishes, download:
   - The Actions artifact with the DOCX, and/or
   - The Release asset automatically published by the workflow.

## Notes
- Special wiki files `_Sidebar.md`, `_Header.md`, `_Footer.md`, `README.md` are excluded from the merged content.
- Image links should resolve automatically via `--resource-path` as long as assets are inside the wiki repo.
- If `_Sidebar.md` contains links like `[[Page Name]]` or `[Text](Page-Name)`, the script will follow that order.