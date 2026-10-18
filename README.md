# 世界信号 / Global Signal

国际新闻中文阅读站：新闻事实、原文链接与潜在信号。静态网站，无需数据库。

## 使用说明
1. 仓库 Actions 里选择 **Update international news**，点击 **Run workflow** 抓取真实新闻。
2. 如需 AI 中文翻译与针对性信号分析，请在仓库 Settings → Secrets and variables → Actions 创建 **OPENAI_API_KEY**；调用 API 可能产生费用。切勿将密钥放入代码。
3. 可选择将仓库发布为静态网站。GitHub Pages 通常为公开可访问站点；请先确认是否同意公开，并检查私人仓库的 Pages 计划支持情况。
4. 暂不公开也能在本地用 `python -m http.server 8000` 浏览。

## 事实与限制
- 每日计划更新两次（UTC 00:23 和 12:23），GitHub Actions 可能延迟。
- 数据从公开 BBC RSS 抓取，并根据关键词和时效性大致排序。
- 无 API Key 时显示英文新闻标题及通用中文类别观察；有 API Key 时可生成中文标题、摘要和针对性信号。
- 观点属于推断，需与原文区分；媒体站点不可用时，任务失败并保留旧数据。
- 提供原始来源链接，未核验每个事件的独立真实性。

## 项目结构
- `index.html` 前端页面（纯 HTML/CSS/JS）
- `data/news.json` 新闻数据
- `scripts/update_news.py` RSS 抓取和可选 AI 分析
- `.github/workflows/daily-news.yml` 定时任务
