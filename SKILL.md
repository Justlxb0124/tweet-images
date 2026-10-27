---
name: tweet-images
description: 把推文、社交媒体帖子或工作流说明做成暖色手绘风配图，使用米白底、衬线标题、陶土橙和终端卡片，默认四张 16:9 PNG。用户要求推文配图、帖子配图、把文案或流程画成图用于发布时使用。适用于 X、即刻、公众号等内容配图；不用于 PPT、数据图表或 App 设计稿。
license: MIT
metadata:
  author: Justlxb0124
  version: "1.0.0"
---

# Tweet images

把用户提供的文案拆成 `spec.json`，用本技能自带的 HTML/CSS/SVG 模板生成图片。保留固定视觉风格，只调整文案和所需版式。

## 环境与路径

- Python 3.8+，运行脚本只用标准库。
- Google Chrome。默认路径为 macOS 的 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`；其他安装位置用环境变量 `CHROME` 指定可执行文件的绝对路径。Chromium 可通过同一变量尝试，未做跨平台验证。
- 字体优先使用 macOS 上的 Songti SC、New York、PingFang SC、Hannotate SC，以及可选的 JetBrains Mono。字体不随仓库分发；缺失时浏览器会回退，排版可能变化。
- 下文命令从包含本文件的技能根目录运行。先确定实际安装目录，使用它的绝对路径，不假设用户的 home 或技能宿主。
- 输出放在用户指定的目录；未指定时，在当前任务工作目录下创建 `output/tweet-images/<主题>/`。不要把用户内容写进技能安装目录。

## 流程

### 1. 拆分内容

默认四张 16:9 图片，用户指定了数量就照办。每张只讲一个观点，标题要能在缩略图里辨认；长文留在帖子正文。

常见安排：观点页用 `split` 加插画，交互示例用 `split` 加终端，步骤用 `flow`，前后差异用 `compare`。这是起点，按内容选择。

忠于原文。名字、术语和命令按用户提供的写，不擅自纠正。编写通用、虚构的终端或 issue 示例时，在交付说明中注明。

### 2. 写 spec

先读 [字段参考](references/spec-format.md)，再复制 [四张完整示例](references/example-spec.json) 到输出目录，按用户文案修改。

优先用现成插画 `bottle`、`magnifier`、`bug`、`doc`、`flag`、`ticket-fan`，以及终端、会话卡、issue、diff 等组件。需要自绘 SVG、使用 `custom` 版式或处理不熟悉的体检问题时，读 [设计规则](references/design-rules.md)。自绘图保存在输出目录，通过相对 spec 的 `svg_file` 引用。

只渲染本次任务生成或已检查的 spec 和 SVG。`custom.html`、内联 SVG 与 `svg_file` 会进入本地浏览器页面，不能把不可信输入当作纯文本数据执行。

### 3. 预览与排版检查

```bash
python3 scripts/build.py /absolute/path/to/output/spec.json
```

输出 `preview/01.png` 等单张图片、`preview/grid.png` 总览，以及逐张体检结果。检查日志中的 `⚠`，修复溢出、超行和孤字，再看总览确认视觉效果。`·` 只是提示，例如命令自动缩字。脚本的退出码不反映排版警告，不能只看退出码判断通过。

每轮把观察到的问题一次改完，再重跑。先看总览，有疑问再看单张。仅重出指定图片可用：

```bash
python3 scripts/build.py /absolute/path/to/output/spec.json --only 2,4
```

`--only` 用于同一份 spec 的局部预览。若改了图片数量或顺序，使用新的输出目录，避免旧 PNG 混进总览。定稿前完整运行一次预览。

### 4. 定稿与交付

```bash
python3 scripts/build.py /absolute/path/to/output/spec.json --final
```

输出到下一个 `vN/`，每张为 3200×1800 PNG，并保存 spec 快照；旧版本保留。定稿也要检查日志和图片，不与 `--only` 混用。

使用当前宿主支持的文件预览、附件或本地文件链接，按顺序交付单张 PNG。总览只用于检查。简短说明每张内容和虚构示例，不自动发布帖子。

修改已有图片时，只改用户指定部分，生成下一版。

## 视觉基线

- 左上角系列名仅显示文字，不加星芒角标。右上角可显示页码。
- 保留米白底、陶土橙、常规字重衬线标题、黑线手绘插画和现有正文组件。
- 修改文案不重写 `assets/style.css` 或现有插画；新增主题或全局样式须有明确需求。
- 不使用品牌 logo、字标或官方口吻。正文中的状态图标与插画装饰保留。
- 目前模板为 16:9。用户需要竖图时，说明需要另做版式，不直接拉伸现有图片。
