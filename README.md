# Wiki to DOCX via GitHub Actions

本仓库提供一个工作流：输入任意 GitHub Wiki 的地址（支持中文与 %xx 编码），自动克隆、合并 Markdown（优先 `_Sidebar.md` 顺序，其次 `Home.md`，再按文件名），用 Pandoc 生成带目录的 DOCX。

## 已修复/增强
- 支持包含中文/空格/%20 的仓库/页面 URL 自动解析为 `.wiki.git`
- 侧边栏中使用绝对 URL 或 `/wiki/` 路径的链接也能正确提取页面名与顺序
- 页面/图片等相对路径中含中文时能更好地匹配本地文件

## 使用方法
1. 将本 README、脚本和工作流文件提交到 `main` 分支（空仓库请先任意提交一次以初始化）。
2. 打开 Actions 选项卡，选择 “Build DOCX from GitHub Wiki”，点击 “Run workflow”。
3. 在弹窗中填写：
   - wiki_url：支持 `.wiki.git`、仓库 URL 或 wiki 页面 URL（可包含中文）
   - output_name：输出 DOCX 文件名（可包含中文与空格）
4. 运行完成后：
   - 在此次运行的页面下载 Artifact（DOCX），或
   - 前往 Releases 页面下载自动发布的附件。