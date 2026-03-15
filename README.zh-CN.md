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

## AI Agent 如何帮助用户使用本项目

如果是一个可以操作浏览器、GitHub 页面或本地仓库的 AI Agent，它最适合在三个阶段协助用户：初始化、部署配置和过滤器迭代。

### 1. 仓库初始化

推荐的 Agent 工作流：

1. 帮用户先 fork 这个仓库，或者如果用户只想本地用，就直接 clone。
2. clone 自己的 fork：
   ```bash
   git clone <your-fork-url>
   cd newsroom
   uv sync --dev
   ```
3. 帮用户创建 `.env`，写入 `GEMINI_API_KEY`。
4. 运行：
   ```bash
   uv run newsroom-gemini-smoke
   uv run pytest
   ```

### 2. GitHub 配置

如果 Agent 可以操作 GitHub 网页，它应该协助用户完成：

1. 将仓库推送到 `main`。
2. 打开仓库设置，确认默认分支是 `main`。
3. 在 `Settings -> Secrets and variables -> Actions` 中添加 `GEMINI_API_KEY`。
4. 如果 GitHub Pages 需要配置来源，则选择 `GitHub Actions`。
5. 确认两个 workflow 都处于可用状态：
   - `.github/workflows/daily-news.yml`
   - `.github/workflows/deploy-pages.yml`

### 3. 如何设计适合自己的过滤器

一个很实用的 Agent 辅助方式是：

1. 先直接使用默认的 `data/FILTER_PROFILE.md`。
2. 让日报先正常跑起来，不要一开始就追求完美过滤器。
3. 如果觉得初始过滤器过宽，Agent 可以帮用户从输出结果里随机抽样一小部分，让用户快速给出 `like / dislike` 反馈。
4. 用户在静态页面中用内置按钮记录反馈。
5. 当样本积累到一定规模后，导出 feedback JSON，放到 `data/feedback/` 下。
6. 运行：
   ```bash
   uv run newsroom-learn-filter --feedback data/feedback/feedback-YYYY-MM-DD.json
   ```
7. 审阅生成的 `data/FILTER_PROFILE.updated.md`，确认没问题后再替换正式过滤器。

### 4. 推荐的反馈闭环

这个项目最适合的，是一个轻量级的每周循环：

1. 平时阅读晨报。
2. 顺手点 `like` 或 `dislike`。
3. 每周导出一次 feedback JSON。
4. 让 Agent 帮你总结：
   - 哪些内容本该拦截却漏了
   - 哪些内容真正有价值，应该被明确保护
5. 运行学习脚本，并审阅候选版 profile。

这样做的好处是：不需要先引入后端，也能让过滤器进入一个可衡量、可回看、可人工审阅的迭代过程。

## 工程文档

- [program_docs/project_structure.md](/Users/golde/code/newsroom/program_docs/project_structure.md)
- [program_docs/module_reference.md](/Users/golde/code/newsroom/program_docs/module_reference.md)
- [program_docs/tdd_strategy.md](/Users/golde/code/newsroom/program_docs/tdd_strategy.md)
- [program_docs/algorithm_notes.md](/Users/golde/code/newsroom/program_docs/algorithm_notes.md)
- [program_docs/ROADMAP.md](/Users/golde/code/newsroom/program_docs/ROADMAP.md)
- [program_docs/agent_playbook.md](/Users/golde/code/newsroom/program_docs/agent_playbook.md)
