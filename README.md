# 世界信号 · Global Signal

永久免费版国际新闻阅读站（原始 RSS 抓取 + 中文规则观察）。仓库已配置定时任务，每日 UTC 00:23 和 12:23 尝试更新，执行可能延迟。

## 功能
- 从 BBC World / Business / Technology / Science & Environment 的 RSS 获取真实标题、摘要与原文链接。
- 分类、关键词搜索和移动端阅读。
- 根据标题摘要关键词自动显示有针对性的中文“信号观察”。这些是规则模板，不能代表经过专业核实的结论。
- 保留英文新闻标题与摘要，以确保没有免费机器翻译服务时不会出现未经验证的中文翻译。
- 免费运行，无需 OpenAI API Key，不会向任何付费 AI API 发请求。

## 使用
1. 在 GitHub Actions → Update international news → Run workflow 手动更新，之后会尝试每天运行两次。
2. 从 data/news.json 检查最新抓取结果。
3. 可用 Python `python -m http.server 8000` 在本地访问主页。
4. GitHub Pages 发布可能需要公开仓库或付费计划支持私有源，**未经同意请不要公开仓库**。

## 注意
新闻排序和类别由关键词规则完成，准确性有限；部分 RSS 可用性取决于媒体服务。每条事件的信号仅为可能性，请点击原文核对事实。