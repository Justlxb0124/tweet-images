# spec.json 字段全集

一份 spec = 一组配图。最快的写法:复制 `example-spec.json`,按新文案改字段。
画布固定 1600×900(定稿 2x = 3200×1800),左右留白 88px,内容区宽 1424px。

## 目录

- 顶层字段
- 行内标记
- 版式 `split` —— 左文右图(论点页、终端示例页)
- 版式 `flow` —— 3~5 步流程
- 版式 `compare` —— 两三栏对比
- 版式 `custom` —— 逃生舱
- 插画库

## 顶层

```jsonc
{
  "kicker": "我的 AI Coding 工作流",   // 每张左上角的系列名,仅显示文字
  "page_numbers": true,                // 右上角 01 / 04,默认开
  "slides": [ ... ]                    // 按顺序,一项一张
}
```

## 行内标记(所有文本字段通用)

| 写法 | 效果 |
|---|---|
| `**粗体**` | 加粗(正文里用来点出关键词) |
| `==强调==` | 陶土橙色字(一张图最多用一处,多了就不稀罕了) |
| `` `命令` `` | 等宽橙色 |
| `\n` | 手动换行 —— 中文断行别交给浏览器,重要句子自己断,避免孤字 |

标题里的全角「：」「，」会自动挤压,不用管。

## 版式 `split`:左文右图

```jsonc
{
  "type": "split",
  "headline": "瓶颈不在模型，\n在==人==。",   // 104px 衬线;默认最多 2 行(headline_lines 可改)
  "headline_size": 104,                     // 可选,放不下时调小(不低于 80)
  "sub": "把脑子里的想法撬出来，\n……",        // 可选,34px 衬线副标题,最多 2 行
  "paras": [                                // 可选,29px 正文段落,每段默认最多 2 行
    {"lead": "模型越来越强：", "text": "……"}
  ],
  "list": ["……**重点**", "……"],            // 可选,编号列表,沉底对齐
  "answer": {"label": "我的最佳实践", "tokens": ["/mattpocock-skills", "GitHub CLI"]},
                                            // 可选,沉底的黑色胶囊;"/" 开头的 token 自动橙色,token 之间自动加 +
  "art": { ... }                            // 右侧彩色卡片,见下
}
```

`art` 两种:

```jsonc
{"color": "clay", "name": "bottle", "params": {...}}      // 插画(卡片宽 600)
{"color": "clay", "svg_file": "illus/xxx.svg"}           // 自绘插画:存成 .svg 文件引用(路径相对 spec.json),别塞进 JSON 字符串里转义
{"type": "terminal", "color": "oat", "title": "~/my-app — claude",   // 深色 Claude Code 终端(卡片宽 760)
 "lines": [
   {"type": "prompt", "cmd": "/wayfinder", "arg": "github.com/…/issues/13"},
   {"type": "gap"},
   {"type": "ai", "chip": "离线保存", "text": "第一行", "cont": ["续行"]},     // chip 可选
   {"type": "options", "items": [{"text": "…", "rec": "推荐", "on": true}, {"text": "…"}]},
   {"type": "user", "text": "用户的回答"},
   {"type": "spinner", "text": "Thinking…"}
 ],
 "input": {"hint": "输入框里的灰字", "mic": true}}      // "input": false 可去掉输入框
```

卡片颜色 `color`:`clay`(陶土橙,主色)/ `oat` / `manilla` / `kraft` / `cactus` / `heather` / `ivory` / `sky`,或直接写 `#RRGGBB`。
一组图里彩色卡片别超过两种颜色。

终端每行宽度:21px 等宽,一个汉字 21px,约 **27 个汉字/行** 放满,超了体检会报。

## 版式 `flow`:流程

```jsonc
{
  "type": "flow",
  "headline": "决策期：一张地图，逐张拷问",        // 78px,默认 1 行,约 17 个汉字放满
  "tag": {"text": "决策 ticket", "style": "outline"},   // 可选;style: outline / clay / olive
  "subtitle": "**你来解决**，终点是一份完整的 spec",    // 可选,1 行
  "stations": [
    {"visual": {...}, "label": {"num": 1, "text": "倒出想法"}, "caption": "两行以内\n的说明"}
  ]
}
```

- 3~5 个站点,站点之间自动画手绘箭头。默认宽度:`window` 300、`issue` 420、`diff` 480、插画 224;可用 `"w": 360` 覆盖。总宽会自动缩放到撑满,站点少时最多放大 1.3 倍并整体居中。
- `label`:`{"num": 1, "text": …}` 黑色圆编号;或 `{"icon": "check" | "ticket" | "spark", "text": …}`。30px,300 宽的站点约放 8 个汉字。
- `caption`:23px,默认最多 2 行(`cap_lines` 可改)。300 宽 ≈ 每行 12 个汉字,420 宽 ≈ 17 个,224 宽 ≈ 9 个。**一律用 `\n` 手动断成两行。**

### 站点视觉 `visual`

**window** —— 浅色会话卡片(Claude Code 风格输入框):

```jsonc
{"type": "window",
 "session": true,                 // 顶部「⊞ 新会话」,默认开;session_label 可改文字
 "prompt": {"cmd": "/implement", "arg": "…/23"},   // 太长会自动缩字,缩到 14px 还放不下体检报错
 "small_prompt": false,           // 小号输入框(stacked 时自动小号)
 "stacked": false,                // 叠放三层卡片 = 「每张都开一个新会话」
 "stamp": "CLOSED",               // 可选,右上角橙色印章
 "blocks": [ ... ]}               // 下面这些块按顺序往下排
```

blocks:

| type | 字段 | 用途 |
|---|---|---|
| `voice` | `text` | 麦克风 + 声波 + 手写体引语,表现「语音随口说」 |
| `qa` | `items: [{"q": "…"}, {"a": "…"}]` | 一问一答气泡(AI 浅底带橙点,人黑底) |
| `log` | `items: [{"text": "…", "state": "done/run/todo"}]` | 带状态图标的进度清单 |
| `out` | `items: ["…", "…"]` | AI 输出的圆点文字行 |
| `illus` | `name` / `params` 或 `svg` | 卡片里放小插画(如 `ticket-fan`) |

**issue** —— GitHub issue / ticket 列表卡:

```jsonc
{"type": "issue", "title": "决策地图：离线同步", "id": "#10", "state": "open",
 "label": "wayfinder:map", "progress": "3/5 closed",    // 有 label 或 progress 才显示进度条行
 "id_first": false,                                      // true 时编号在行首(任务列表风格)
 "rows": [{"text": "…", "id": "#11", "state": "done", "badge": {"text": "已合并", "tone": "ok"}, "dep": "← #23"}]}
```

state:`done`(橙底白勾)/ `open`(橄榄绿圈)/ `run`(橙色 ✻,进行中)/ `todo`(灰圈)。badge tone:`ok` 绿 / `run` 橙 / 不写为灰。4~5 行最合适。

**diff** —— 代码改动卡片(PR / review 类内容):

```jsonc
{"type": "diff", "title": "Files changed · 12", "stat": {"add": "+86", "del": "−41"},
 "files": [{"file": "db/migrations/0007_orders.sql", "tag": "数据结构变更",
            "lines": [{"sign": "+", "code": "ALTER TABLE orders ADD note TEXT;"}]}],
 "more": "··· 其余 9 个文件"}
```

默认宽 480(用 `w` 改)。sign 取 `+` 绿底、`-` 红底、空格为普通行。3 个文件、每个 1 行最合适。

**illus** / **svg** —— 独立插画:`{"type": "illus", "name": "doc", "params": {"title": "spec.md"}}`;自绘的用 `{"type": "svg", "svg_file": "illus/xxx.svg"}`(路径相对 spec.json)。

## 版式 `compare`:对比

```jsonc
{"type": "compare", "headline": "review 的重点，==变了==", "subtitle": "…", "ratio": [1, 1.25],
 "columns": [
   {"tag": "以前", "title": "代码写得对不对", "items": ["挑语法", "挑风格"], "muted": true},
   {"tag": {"text": "现在", "style": "clay"}, "title": "做的事对不对", "color": "clay-soft",
    "items": ["它有没有**理解需求**", "**边界条件**漏没漏", "…"]}
 ]}
```

- 2~3 栏。每栏:标签、56px 衬线标题(默认 1 行,`title_lines` 可改),下面是沉底的编号条目(31px,默认每条 1 行,`item_lines` 可改)。
- `muted: true` 表示「旧的 / 被否定的」一栏,编号和文字会变灰。`ratio` 控制栏宽比例,重点栏给宽一点。
- `color` 用卡片色,另有 `dark`(深色终端色)。每栏 2~4 条最合适。

## 版式 `custom`:逃生舱

```jsonc
{"type": "custom", "headline": "…", "subtitle": "…", "html": "<div style='position:absolute;left:88px;top:322px'>…</div>"}
```

以上都套不上时才用。可以复用 style.css 里的 class(`.card` `.prompt` `.issue` `.tag` `.pill` …);给需要体检的元素加 `data-fit`(不许超出最近的 `data-box` 祖先)或 `data-maxlines="2"`。

## 插画库(`name`)

| name | 画布 | params | 画的是 |
|---|---|---|---|
| `bottle` | 600×718(split 右卡) | `right_title` `right_sub` `left_title` `left_sub` `mark` | 瓶子 = 瓶颈;瓶身装满星星,瓶口卡着「?」 |
| `doc` | 224×318 | `title` | 带蓝图示意和完成勾的文档(spec / 方案 / 文档类) |
| `flag` | 224×318 | — | 小山坡插旗 = 交付 / 上线 / 达成 |
| `ticket-fan` | 256×170(卡片内) | — | 文档 → 拆成一叠票 |
| `magnifier` | 600×718(split 右卡) | `note`(左上小注) `title` `sub`(右侧手写标注) | 放大镜看一页代码 = 审查 / 检查 / 细看 |
| `bug` | 600×718(split 右卡) | `question`(黑气泡) `answer`(白气泡) `label` `note` | 支支吾吾的回答后面藏着虫 = 隐患 / 说不清的地方 |

库里没有合适的,就按 design-rules.md 的手绘配方自绘,存成 `.svg` 文件,用 `svg_file` 引用。
