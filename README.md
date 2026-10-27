# Tweet images

把一段推文，变成一组可以直接发布的配图。

米白底、陶土橙、衬线大标题、黑线手绘插画。AI 负责拆分内容和编写 JSON，固定模板负责排版，Chrome 负责导出 PNG。适合分享 AI Coding 实践、讲解工作流、展示终端交互和对比方案。

An open-source Agent Skill for turning social posts into warm, illustrated image sets. JSON in, publication-ready PNGs out.

[安装](#安装) · [实际效果](#实际效果) · [直接运行](#不使用-agent直接运行) · [字段参考](references/spec-format.md) · [MIT](LICENSE)

## 实际效果

以下两组来自作者 [@lxxbbb_bonnie](https://x.com/lxxbbb_bonnie) 已发布的推文。图片保存在仓库内，点击可查看大图。

这些是历史原图，保留了当时的角标。**当前模板已去掉左上角星芒，只保留系列标题文字**；配色、字体和其他样式延续原版。

### 从想法到交付的 AI Coding 工作流

把长推文里的思考与执行过程分成四张：开发瓶颈、通过问答补全决策、整理需求、拆分实施任务。

[阅读原推文](https://x.com/lxxbbb_bonnie/status/2104180881455796669) · [可运行的示例 spec](references/example-spec.json)

| 01 · 开篇观点 | 02 · 交互示例 |
| --- | --- |
| [![开发瓶颈与模型能力](examples/published/ai-coding-workflow/01.jpg)](examples/published/ai-coding-workflow/01.jpg) | [![通过问答补全决策](examples/published/ai-coding-workflow/02.jpg)](examples/published/ai-coding-workflow/02.jpg) |
| **03 · 决策流程** | **04 · 实施流程** |
| [![把决策汇总为 spec](examples/published/ai-coding-workflow/03.jpg)](examples/published/ai-coding-workflow/03.jpg) | [![把 spec 拆成任务并实施](examples/published/ai-coding-workflow/04.jpg)](examples/published/ai-coding-workflow/04.jpg) |

### 跨会话协作

用一组配图解释多个 AI 会话如何交流，呈现共享文件传话与直接发送消息的差异。

[阅读原推文](https://x.com/lxxbbb_bonnie/status/2106987761400197152) · 本组收录发布时的四张图片，未附原始 spec。

| 01 | 02 |
| --- | --- |
| [![跨会话协作示例第一张](examples/published/cross-session-collaboration/01.jpg)](examples/published/cross-session-collaboration/01.jpg) | [![跨会话协作示例第二张](examples/published/cross-session-collaboration/02.jpg)](examples/published/cross-session-collaboration/02.jpg) |
| **03** | **04** |
| [![跨会话协作示例第三张](examples/published/cross-session-collaboration/03.jpg)](examples/published/cross-session-collaboration/03.jpg) | [![跨会话协作示例第四张](examples/published/cross-session-collaboration/04.jpg)](examples/published/cross-session-collaboration/04.jpg) |

## 它能做什么

- 默认输出四张 16:9 图片，也可按内容调整张数。
- 预览为 1600×900，定稿为 3200×1800 PNG，并生成四宫格或多行总览。
- 提供四种版式和六种内置插画，不需要每次重写 HTML/CSS。
- 自动检查文字越界、超行和孤字，辅助人工检查排版。
- 定稿保存为 `v1/`、`v2/` 等独立目录，方便保留和比较版本。
- 渲染脚本只依赖 Python 标准库与本地 Chrome，不需要图像生成 API。

| 版式 | 适合内容 | 常用组件 |
| --- | --- | --- |
| `split` | 开篇观点、概念、对话示例 | 左侧文字，右侧插画或终端 |
| `flow` | 流程、步骤、任务拆解 | 会话卡、issue、diff、箭头 |
| `compare` | 前后变化、方案差异 | 两至三栏对比卡片 |
| `custom` | 内置版式无法表达的内容 | 自定义 HTML，复用现有样式 |

## 安装

本仓库按 [Agent Skills 标准](https://agentskills.io/specification) 组织，根目录的 `SKILL.md` 是技能入口，脚本、素材和参考资料均随仓库提供。

### 通过 skills CLI

安装了 Node.js 和 npm 后，可以使用 [skills CLI](https://skills.sh/docs/cli)：

```bash
npx skills add Justlxb0124/tweet-images
```

按提示选择你的 agent 和安装范围。安装技能后仍需准备下面的 Python 和 Chrome 运行环境。

### 手动安装

```bash
git clone https://github.com/Justlxb0124/tweet-images.git
```

把完整的 `tweet-images/` 目录放进你的 agent 支持的技能目录，或让 agent 读取其中的 `SKILL.md`。不要只复制入口文件，脚本需要同目录下的 `assets/` 和 `references/`。

### 运行环境

| 项目 | 要求 |
| --- | --- |
| Python | 3.8 或更新版本，无第三方 Python 运行依赖 |
| 浏览器 | Google Chrome，脚本以无头模式调用 |
| 已验证平台 | macOS |
| 字体 | 优先使用系统宋体、New York、PingFang SC、Hannotate SC；等宽字体可用 JetBrains Mono |

默认 Chrome 路径是 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。安装在其他位置时，设置 `CHROME` 为可执行文件的绝对路径：

```bash
export CHROME="/absolute/path/to/chrome"
```

仓库不分发字体。缺少字体时会使用浏览器回退字体，中文断行与手写效果可能不同。Linux、Windows 和 Chromium 尚未验证；设置浏览器路径后仍需自行检查字体与排版。

## 在 agent 中使用

安装后，把文案贴给 agent：

```text
用 tweet-images 给下面这段推文做 4 张配图。
保持暖色手绘风，输出到 ./output/my-post。

[粘贴你的推文]
```

也可以指定重点：

```text
把这段工作流做成配图：第一张讲观点，第二张做前后对比，
第三、四张拆解步骤。每张只讲一件事，命令名保留原文。
```

后续修改可以直接说：

```text
第二张的标题改为「会话之间，直接对话」。其他图片保持不变。
```

Agent 会拆分内容、写 spec、生成预览、检查排版，再导出定稿。技能不会替你发布推文。

## 不使用 agent，直接运行

下面的命令在仓库根目录执行。先把示例复制到输出目录，避免生成文件混进技能本身：

```bash
mkdir -p output/demo
cp references/example-spec.json output/demo/spec.json
python3 scripts/build.py output/demo/spec.json
```

打开 `output/demo/preview/grid.png` 看整体效果，再检查单张图片和终端日志。确认后生成高清版本：

```bash
python3 scripts/build.py output/demo/spec.json --final
```

输出结构：

```text
output/demo/
├── spec.json
├── .build/          # 中间 HTML，引用本地技能样式
├── preview/
│   ├── 01.png … 04.png
│   └── grid.png
└── v1/
    ├── 01.png … 04.png
    ├── grid.png
    └── spec.json    # 本次定稿的输入快照
```

再次执行 `--final` 会创建 `v2/`。发布时使用各张 PNG；`grid.png` 是检查用的总览。`.build/` 中的 HTML 使用本地路径，不能单独当作可移植网页分发。

仅重出第二、四张预览：

```bash
python3 scripts/build.py output/demo/spec.json --only 2,4
```

`--only` 使用从 1 开始的图片编号，用于同一份 spec 的局部修改。图片数量或顺序变化时，请换一个输出目录；定稿前完整重跑一次，不要把 `--only` 与 `--final` 混用。

### 最小 spec

保存下面的内容为输出目录中的 `spec.json`，即可生成一张图：

```json
{
  "kicker": "我的工作流",
  "page_numbers": true,
  "slides": [
    {
      "type": "split",
      "headline": "把想法\n变成==配图==。",
      "sub": "每张讲清一个观点，\n让读者一眼看懂。",
      "art": {
        "name": "magnifier",
        "color": "oat",
        "params": {
          "note": "看清重点",
          "title": "一个观点",
          "sub": "一张图"
        }
      }
    }
  ]
}
```

完整字段和组件示例见 [spec-format.md](references/spec-format.md)。`**粗体**`、`==强调色==`、反引号包裹的命令和 `\n` 换行都可在相应文本字段中使用。

## 排版检查与常见问题

**日志中的 `⚠` 需要处理。** 它可能表示文字越界、超过指定行数或出现孤字。优先缩短文字、手动换行或拆成另一张图片。`·` 是提示，例如长命令自动缩字。脚本退出码为 0 不代表没有排版警告，验收时需要同时检查日志和图片。

**提示找不到 Chrome。** 检查默认路径，或用 `CHROME` 指向实际可执行文件。先确认浏览器可以在本机正常启动。

**中文效果与示例不一致。** 检查字体。重要句子用 `\n` 指定断行；字体回退会改变字宽，不能只照着字符数量估算。

**预览出现旧图。** 复用目录并减少图片数量可能留下旧 PNG。为新的一组图片使用新目录；局部修改只用于同一组内容。

**需要竖图。** 目前模板只支持 16:9。3:4 或 9:16 需要新增版式，不宜拉伸现有 PNG。

**能否渲染任意 JSON？** 只渲染自己生成或检查过的 spec。自定义 HTML、内联 SVG 和 `svg_file` 会进入本地 Chrome，脚本并不是处理不可信输入的隔离环境。

## 目录与贡献

```text
tweet-images/
├── SKILL.md                    # 给 agent 的入口和操作流程
├── scripts/build.py            # HTML、截图、总览与排版体检
├── assets/style.css            # 固定视觉样式
├── references/
│   ├── spec-format.md          # 字段与组件说明
│   ├── example-spec.json       # 四张完整示例
│   └── design-rules.md         # 视觉规范与自绘 SVG 指引
├── examples/published/         # 两条推文的历史原图与来源说明
├── README.md
└── LICENSE
```

欢迎提交新的插画、版式或排版修复。改动样式或渲染逻辑时，请附最小 spec、修改前后图片和运行环境，说明哪些视觉效果发生了变化。

现有基线是米白底、陶土橙、衬线标题、黑线手绘插画，以及左上角纯文字系列名。修复局部问题时保留其余已确认样式。示例中的命令、产品行为和文案属于发布当时的内容，不作为第三方产品的最新文档。

## 许可与来源

[MIT License](LICENSE)。作者：[Lxxbbb](https://x.com/lxxbbb_bonnie) / [Justlxb0124](https://github.com/Justlxb0124)。

设计借鉴了暖色编辑排版与手绘技术插画，原模板也参考过 Claude 的视觉语言。本项目是个人作品，与 Anthropic、OpenAI 或 X 无隶属关系。产品名称与商标归各自所有者所有；许可证不授予这些商标的使用权。示例图片及原帖链接见 [来源清单](examples/published/README.md)。
