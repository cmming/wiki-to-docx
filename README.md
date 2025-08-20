# Wiki to DOCX via GitHub Actions

本仓库提供一个工作流：输入任意 GitHub Wiki 的地址，自动克隆、合并 Markdown（优先 `_Sidebar.md` 顺序，其次 `Home.md`，再按文件名），用 Pandoc 生成带目录的 DOCX。

## 支持的地址形式
- 直接的 `.wiki.git`：`https://github.com/owner/repo.wiki.git`
- 仓库主页 URL：`https://github.com/owner/repo`
- Wiki 页面 URL：`https://github.com/owner/repo/wiki/Some-Page`
- 兼容 `git@` 形式（会转换为 `repo.wiki.git`）

脚本会自动将上述 URL 规范化为对应的 `repo.wiki.git` 并进行克隆。

## 使用方法
1. 将本 README、脚本和工作流文件提交到 `main` 分支（空仓库请先任意提交一次以初始化）。
2. 打开 Actions 选项卡，选择 “Build DOCX from GitHub Wiki”，点击 “Run workflow”。
3. 在弹窗中填写：
   - wiki_url：支持 `.wiki.git`、仓库 URL 或 wiki 页面 URL
   - output_name：输出 DOCX 文件名（例如 `coze-studio-wiki.docx`）
4. 运行完成后：
   - 在此次运行的页面下载 Artifact（DOCX），或
   - 前往 Releases 页面下载自动发布的附件。

## 说明
- 排序规则：Sidebar 链接顺序 > Home.md > 其他按字母序（忽略 `_Sidebar.md`, `_Header.md`, `_Footer.md`, `README.md`）。
- 资源解析：通过 `--resource-path` 确保图片等资源能被 Pandoc 正确打包。
- 样式扩展：如需自定义样式，可使用 `--reference-docx` 传入模板文件，并在工作流中补充输入参数。