# Newsroom

[English Version](./README.md)

Newsroom 是一个基于 Gemini 的每日技术情报流水线。它负责抓取 RSS、筛选并翻译新闻、发布 GitHub Pages 静态晨报，并支持基于本地反馈 JSON 持续迭代纯文本过滤器。

## 目录结构

```text
src/newsroom/        Python 源代码
tests/               pytest 测试
data/                过滤器、原始 RSS 数据、反馈导出、学习产物
docs/                GitHub Pages 静态站点
program_docs/        项目工程文档
.github/workflows/   自动化工作流
```

## 快速开始

1. 用 uv 安装依赖：
   ```bash
   uv sync --dev
   ```
2. 在项目根目录创建 `.env`：
   ```dotenv
   GEMINI_API_KEY=your_api_key
   ```
3. 抓取 RSS：
   ```bash
   uv run newsroom-fetch
   ```
4. 运行筛选与发布：
   ```bash
   uv run newsroom-filter
   ```
5. 运行测试：
   ```bash
   uv run pytest
   ```

## 常用命令

- `uv run newsroom-fetch`
  抓取 RSS 到 `data/raw_news.json`。
- `uv run newsroom-filter`
  执行筛选、排序、翻译，并生成 `docs/data/news.json`。
- `uv run newsroom-learn-filter --feedback data/feedback/feedback-YYYY-MM-DD.json`
  基于反馈 JSON 学习过滤器，生成候选新版 profile。
- `uv run newsroom-gemini-smoke`
  快速验证 Gemini API key 是否可用。

## 数据文件

- `data/FILTER_PROFILE.md`
  当前纯文本过滤协议。
- `data/raw_news.json`
  最近一次抓取的 RSS 原始数据。
- `data/feedback/*.json`
  页面导出的本地反馈 JSON，默认不会提交到 Git。
- `data/FILTER_PROFILE.updated.md`
  学习脚本生成的候选新版过滤器。
- `data/FILTER_PROFILE.learning_report.md`
  学习阶段的诊断信息和原始模型输出。

## GitHub 自动化

- `.github/workflows/daily-news.yml`
  每日自动抓取、筛选并提交新的静态数据。
- `.github/workflows/deploy-pages.yml`
  将 `docs/` 自动部署到 GitHub Pages。

## 工程文档

- [program_docs/project_structure.md](/Users/golde/code/newsroom/program_docs/project_structure.md)
- [program_docs/module_reference.md](/Users/golde/code/newsroom/program_docs/module_reference.md)
- [program_docs/tdd_strategy.md](/Users/golde/code/newsroom/program_docs/tdd_strategy.md)
- [program_docs/algorithm_notes.md](/Users/golde/code/newsroom/program_docs/algorithm_notes.md)
- [program_docs/ROADMAP.md](/Users/golde/code/newsroom/program_docs/ROADMAP.md)
