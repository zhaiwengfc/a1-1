# A1 产业门户 · 01【低空信息站】 (`zhaiwengfc/a1-1`)

本项目为 **A1 产业门户 · 01【低空信息站】** 生产环境前端与每日自动化内容更新工程，对应仓库 [`https://github.com/zhaiwengfc/a1-1`](https://github.com/zhaiwengfc/a1-1)。

## 一、 核心架构与运行机制

1. **视觉与交互设计**：
   - 全站采用白底、分区疏密黑点阵列、黄色黑框立体按键与滚动章节吸附（Scroll-Snap）设计。
   - 顶栏仅保留跨板块总导航（01 低空信息站、02 空域智算网等），低空信息站专属**收藏夹**内嵌于板块内部，前后台严格分离。
2. **每日 `07:00` 行业资讯自动同步 (`scripts/daily_crawler.py`)**：
   - 每日北京时间 `06:35` 启动采集清洗，于 `07:00` 准时将【政策法规】、【创新与供应链信息】、【比赛信息】、【产品发布】四大栏目的最新政务、主流媒体与行业动态写入 `data/news.json` 并发布上线。
3. **每日 `09:00` A1 新闻部深度特稿发布 (`scripts/daily_newsroom_writer.py`)**：
   - 一周七天每日 `09:00` 准时发布 1 篇由“A1 新闻部”撰写的深度专栏文章。
   - 自动根据当日行业焦点动态确定所属栏目，并配套生成多维度互动专题看板组件（`creativeWidget`）。

## 二、 目录结构（最精简生产态）

```text
a1-1/
├── index.html                           # 门户主页面
├── data/
│   └── news.json                        # 四大栏目资讯与 A1新闻部数据
├── scripts/
│   ├── daily_crawler.py                 # 每日 07:00 四大栏目资讯同步脚本
│   └── daily_newsroom_writer.py         # 每日 09:00 A1新闻部生成脚本
├── .github/
│   └── workflows/
│       └── a1_auto_pipeline.yml         # GitHub Actions 双定时自动流水线
└── .nojekyll                            # GitHub Pages 静态直通配置                            # GitHub Pages 静态直通配置
```

## 三、 部署与启用步骤

1. 将解压后的全部文件上传并提交至 `zhaiwengfc/a1-1` 仓库 `main` 分支。
2. 进入仓库 **Settings** ➔ **Actions** ➔ **General** ➔ **Workflow permissions**，勾选 **Read and write permissions** 并保存。
3. （可选）如需接入云端大模型生成每日特稿，可在 **Settings** ➔ **Secrets and variables** ➔ **Actions** 中添加 `GEMINI_API_KEY`；未配置时将自动使用内置专栏生成模块。
