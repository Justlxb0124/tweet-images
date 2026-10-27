#!/usr/bin/env python3
"""tweet-images: spec.json -> 每张一个 HTML -> 无头 Chrome 出 PNG + 四宫格预览 + 排版体检。

用法:
  build.py SPEC.json                 # 预览:1x 出图到 <spec 目录>/preview/,拼 grid.png,打印体检结果
  build.py SPEC.json --final         # 定稿:2x 出图到 <spec 目录>/vN/(N 自动递增,不覆盖旧版)
  build.py SPEC.json --only 2,4      # 只重出第 2、4 张(预览模式下用于局部返工)

spec 格式见 ../references/spec-format.md。
"""
import argparse, html as H, json, math, os, re, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(SKILL, 'assets', 'style.css')
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
COLORS = {'clay': '#D97757', 'oat': '#E3DACC', 'manilla': '#EBDBBC', 'kraft': '#D4A27F', 'cactus': '#BCD1CA',
          'heather': '#CBCADB', 'ivory': '#F0EEE6', 'dark': '#1F1E1D', 'clay-soft': '#F5E1D8', 'sky': '#DCE7F1'}
INNER_W = 1424  # 1600 - 左右各 88
SPEC_DIR = '.'  # main() 里设为 spec 所在目录,svg_file 相对它解析

# ---------------------------------------------------------------- text helpers
def esc(s):
    return H.escape(str(s), quote=False)

def md(s, head=False):
    """轻量标记:**粗体**  ==强调色==  `命令`  \\n 换行。head=True 时挤压标题里的全角：，"""
    s = esc(s)
    if head:
        s = s.replace('：', '<span class="pc">：</span>').replace('，', '<span class="pm">，</span>')
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'==(.+?)==', r'<span class="accent">\1</span>', s)
    s = re.sub(r'`(.+?)`', r'<code class="ic">\1</code>', s)
    return s.replace('\n', '<br>')

def color(c, default):
    return COLORS.get(c or default, c or COLORS[default])

# ---------------------------------------------------------------- shared svg bits
ASTER = ('<svg viewBox="-13 -13 26 26"><g stroke="#D97757" stroke-width="3.4" stroke-linecap="round">'
         '<path d="M0-10V10M-10 0H10M-7.1-7.1L7.1 7.1M-7.1 7.1L7.1-7.1"/></g></svg>')
DEFS = '''<svg width="0" height="0" style="position:absolute"><defs>
  <filter id="rough" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3.5" xChannelSelector="R" yChannelSelector="G"/></filter>
  <filter id="rough-lg" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4.5" xChannelSelector="R" yChannelSelector="G"/></filter>
  <symbol id="i-done" viewBox="0 0 22 22"><circle cx="11" cy="11" r="10" fill="#D97757"/><path d="M6.5 11.2l3 3 6-6.2" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="i-open" viewBox="0 0 22 22"><circle cx="11" cy="11" r="8.5" fill="none" stroke="#788C5D" stroke-width="2.4"/><circle cx="11" cy="11" r="2.8" fill="#788C5D"/></symbol>
  <symbol id="i-todo" viewBox="0 0 22 22"><circle cx="11" cy="11" r="8.5" fill="none" stroke="#B0AEA5" stroke-width="2.4"/></symbol>
  <symbol id="i-run" viewBox="-13 -13 26 26"><g stroke="#D97757" stroke-width="3.4" stroke-linecap="round"><path d="M0-10V10M-10 0H10M-7.1-7.1L7.1 7.1M-7.1 7.1L7.1-7.1"/></g></symbol>
</defs></svg>'''
MIC = ('<svg width="{w}" height="{h}" viewBox="0 0 26 30" fill="none" stroke="#D97757" stroke-width="2.7" stroke-linecap="round">'
       '<rect x="8" y="2" width="10" height="17" rx="5"/><path d="M3 14c0 5.5 4.5 9.5 10 9.5s10-4 10-9.5M13 24v4"/></svg>')
ARROW = ('<svg class="arr" style="left:{x}px" viewBox="0 0 60 318"><g filter="url(#rough)" fill="none" stroke="#73726C" '
         'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 162 C22 154 34 168 48 159"/>'
         '<path d="M38 150 L50 158 L40 169"/></g></svg>')
LABEL_ICONS = {
    'check': ('clay', '<svg width="22" height="22" viewBox="0 0 22 22"><path d="M5 11.5l4 4 8-8.5" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    'ticket': ('outline', '<svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="#141413" stroke-width="2.2" stroke-linejoin="round"><path d="M2 6h18v3a2 2 0 0 0 0 4v3H2v-3a2 2 0 0 0 0-4z"/><path d="M8 7v8" stroke-dasharray="2 2"/></svg>'),
    'spark': ('outline', ASTER.replace('<svg ', '<svg width="20" height="20" ')),
}

def state_icon(state, size=22):
    sid = {'done': 'i-done', 'open': 'i-open', 'run': 'i-run', 'todo': 'i-todo'}.get(state or 'todo', 'i-todo')
    return f'<svg width="{size}" height="{size}"><use href="#{sid}"/></svg>'

# ---------------------------------------------------------------- illustration library
def illus_bottle(p):
    rt, rs = p.get('right_title', '人的决策'), p.get('right_sub', '')
    lt, ls = p.get('left_title', '模型能力'), p.get('left_sub', '')
    mark = esc(p.get('mark', '?'))
    body = "M266 150 L266 272 C266 320 120 332 120 402 L120 572 C120 608 146 622 180 622 L420 622 C454 622 480 608 480 572 L480 402 C480 332 334 320 334 272 L334 150 Z"
    stars_c = [(196, 520, 34), (318, 494, 22), (410, 548, 36), (290, 574, 18), (168, 588, 14), (420, 478, 13)]
    stars_i = [(236, 404, 16), (372, 392, 20), (300, 350, 12), (508, 470, 18), (92, 520, 12)]
    st = lambda xs: ''.join(f'<path data-star="{x},{y},{r}"/>' for x, y, r in xs)
    return f'''<svg viewBox="0 0 600 718" preserveAspectRatio="xMidYMid meet">
<defs><clipPath id="bottle-body"><path d="{body}"/></clipPath></defs>
<g filter="url(#rough-lg)" stroke="#141413" stroke-linejoin="round" stroke-linecap="round">
  <ellipse cx="300" cy="636" rx="206" ry="15" fill="#141413" fill-opacity=".16" stroke="none"/>
  <path d="{body}" fill="#FAF9F5" stroke-width="5.5"/>
  <g clip-path="url(#bottle-body)"><path d="M110 452 C160 436 200 468 250 452 C300 436 340 468 390 452 C430 440 460 460 500 450 L500 640 L110 640 Z" fill="#EBDBBC" stroke="none"/>
  <path d="M110 452 C160 436 200 468 250 452 C300 436 340 468 390 452 C430 440 460 460 500 450" fill="none" stroke-width="4"/></g>
  <g fill="#D97757" stroke-width="3.2">{st(stars_c)}</g>
  <g fill="#FAF9F5" stroke-width="3">{st(stars_i)}</g>
  <g fill="#141413" stroke="none"><circle cx="352" cy="604" r="5"/><circle cx="238" cy="604" r="4"/><circle cx="452" cy="598" r="4"/><circle cx="154" cy="486" r="3.5"/><circle cx="262" cy="530" r="3.5"/></g>
  <rect x="248" y="118" width="104" height="36" rx="11" fill="#FAF9F5" stroke-width="5.5"/>
  <g font-family="Hannotate SC" font-size="46" font-weight="700" fill="#141413" stroke="none" text-anchor="middle">
    <text x="300" y="206" transform="rotate(-10 300 190)">{mark}</text><text x="302" y="254" transform="rotate(9 302 238)">{mark}</text>
    <text x="298" y="300" transform="rotate(-5 298 284)">{mark}</text><text x="262" y="330" font-size="34" transform="rotate(-18 262 318)">{mark}</text>
    <text x="340" y="334" font-size="34" transform="rotate(14 340 322)">{mark}</text></g>
  <g fill="none" stroke-width="3.5"><path d="M392 198 C372 196 358 204 346 222"/><path d="M344 208 L345 224 L360 219"/>
    <path d="M84 320 C88 384 108 432 150 474"/><path d="M133 468 L151 475 L153 457"/></g>
  <g font-family="Hannotate SC" font-size="36" font-weight="700" fill="#141413" stroke="none">
    <text x="402" y="196">{esc(rt)}</text><text x="402" y="238" font-size="26" font-weight="400">{esc(rs)}</text>
    <text x="40" y="262">{esc(lt)}</text><text x="40" y="298" font-size="26" font-weight="400">{esc(ls)}</text></g>
</g></svg>'''

def illus_doc(p):
    title = esc(p.get('title', 'spec.md'))
    return f'''<svg viewBox="0 0 224 318" preserveAspectRatio="xMidYMid meet"><g filter="url(#rough)" stroke="#141413" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">
  <ellipse cx="116" cy="306" rx="88" ry="8" fill="#141413" fill-opacity=".1" stroke="none"/>
  <path d="M26 16 H158 L198 56 V298 H26 Z" fill="#FFFFFF"/><path d="M158 16 V56 H198" fill="#EBDBBC"/>
  <text x="46" y="84" font-family="JetBrainsMono Nerd Font, Menlo" font-size="22" font-weight="600" fill="#141413" stroke="none">{title}</text>
  <path d="M46 110 H176 M46 132 H158 M46 154 H170" stroke="#B0AEA5" stroke-width="4"/>
  <rect x="46" y="176" width="130" height="92" rx="8" fill="#E4EDF5" stroke="#6A9BCC" stroke-width="3"/>
  <path d="M58 196 H96 V222 H58 Z M114 196 H162 M114 212 H150 M58 244 H162" stroke="#6A9BCC" stroke-width="3" fill="none"/>
  <circle cx="186" cy="274" r="24" fill="#D97757"/><path d="M175 274.5 l7.5 7 l13-14" fill="none" stroke="#FFFFFF" stroke-width="4.2"/>
</g></svg>'''

def illus_flag(p):
    return '''<svg viewBox="0 0 224 318" preserveAspectRatio="xMidYMid meet"><g filter="url(#rough)" stroke="#141413" stroke-width="4.5" stroke-linejoin="round" stroke-linecap="round">
  <path d="M8 300 C40 238 184 238 216 300 Z" fill="#EBDBBC"/><path d="M84 256 V40"/>
  <path d="M84 44 C112 30 136 60 164 48 C176 43 186 40 196 42 L196 124 C170 118 150 140 124 132 C108 127 96 124 84 128 Z" fill="#D97757"/>
  <path d="M122 84 l12 12 l24-26" fill="none" stroke="#FAF9F5" stroke-width="6"/><circle cx="84" cy="36" r="7" fill="#141413"/></g>
  <g filter="url(#rough)" fill="#FAF9F5" stroke="#141413" stroke-width="3" stroke-linejoin="round">
  <path data-star="36,110,18"/><path data-star="190,190,14"/><path data-star="46,196,10"/></g></svg>'''

def illus_ticket_fan(p):
    rows = [(-6, 18), (3, 56), (-3, 94), (5, 132)]
    tk = ''.join(f'<g transform="rotate({a} 204 {y+13})"><path d="M162 {y} H246 V{y+26} H162 Z" fill="#FAF9F5"/><rect x="166" y="{y+5}" width="12" height="16" rx="2" fill="#D97757" stroke="none"/></g>' for a, y in rows)
    return f'''<svg viewBox="0 0 256 170"><g filter="url(#rough)" stroke="#141413" stroke-width="3.4" stroke-linejoin="round" stroke-linecap="round">
  <path d="M14 22 H74 L96 44 V150 H14 Z" fill="#FFFFFF"/><path d="M74 22 V44 H96" fill="#EBDBBC"/>
  <path d="M28 64 H82 M28 82 H74 M28 100 H80 M28 118 H66" stroke="#B0AEA5" stroke-width="3.2"/>
  <path d="M108 86 C122 80 132 92 146 86" fill="none" stroke="#73726C" stroke-width="3"/><path d="M138 78 L148 86 L139 95" fill="none" stroke="#73726C" stroke-width="3"/>
  {tk}</g></svg>'''


def illus_magnifier(p):
    note, t1, t2 = esc(p.get('note', '语法 ✓　风格 ✓')), esc(p.get('title', '做的事')), esc(p.get('sub', '对不对？'))
    return f"""<svg viewBox='0 0 600 718' preserveAspectRatio='xMidYMid meet'>
<defs><clipPath id='lens-clip'><circle cx='392' cy='456' r='104'/></clipPath></defs>
<g filter='url(#rough-lg)' stroke='#141413' stroke-linejoin='round' stroke-linecap='round'>
  <ellipse cx='300' cy='648' rx='214' ry='15' fill='#141413' fill-opacity='.16' stroke='none'/>
  <g transform='rotate(-4 240 380)'><path d='M76 138 H330 L386 194 V612 H76 Z' fill='#FFFFFF' stroke-width='5.5'/><path d='M330 138 V194 H386' fill='#EBDBBC' stroke-width='5'/>
    <g stroke='#B0AEA5' stroke-width='7' fill='none'><path d='M112 222 H236'/><path d='M140 258 H312'/><path d='M140 294 H280'/><path d='M168 330 H336'/><path d='M140 366 H252'/><path d='M112 402 H188'/><path d='M112 462 H270'/><path d='M140 498 H330'/><path d='M140 534 H290'/><path d='M112 570 H210'/></g></g>
  <g transform='rotate(45 392 456)'><rect x='512' y='438' width='132' height='36' rx='16' fill='#141413' stroke-width='5.5'/><rect x='496' y='440' width='30' height='32' rx='6' fill='#EBDBBC' stroke-width='4.5'/></g>
  <circle cx='392' cy='456' r='122' fill='#FAF9F5' stroke-width='5.5'/>
  <g clip-path='url(#lens-clip)'><rect x='270' y='432' width='250' height='50' fill='#EBDBBC' stroke='none'/>
    <g fill='none' stroke-width='12'><path d='M300 396 H440' stroke='#B0AEA5'/><path d='M318 457 H470' stroke='#141413'/><path d='M300 518 H410' stroke='#B0AEA5'/></g></g>
  <circle cx='392' cy='456' r='104' fill='none' stroke-width='3.5'/>
  <g font-family='Hannotate SC' fill='#141413' stroke='none'><text x='426' y='208' font-size='36' font-weight='700'>{t1}</text><text x='426' y='248' font-size='26'>{t2}</text><text x='84' y='106' font-size='27' fill='#3D3D3A'>{note}</text></g>
  <g fill='none' stroke-width='3.5'><path d='M470 262 C486 286 482 306 466 326'/><path d='M462 308 L464 328 L481 322'/></g>
  <g fill='#FAF9F5' stroke-width='3'><path data-star='40,300,17'/><path data-star='556,120,20'/><path data-star='560,370,12'/><path data-star='36,560,12'/></g>
</g></svg>"""

def illus_bug(p):
    q, a = esc(p.get('question', '为什么这么写？')), esc(p.get('answer', '因为……呃……'))
    lb, nt = esc(p.get('label', 'bug 藏在这')), esc(p.get('note', '解释不清'))
    return f"""<svg viewBox='0 0 600 718' preserveAspectRatio='xMidYMid meet'>
<g filter='url(#rough-lg)' stroke='#141413' stroke-linejoin='round' stroke-linecap='round'>
  <path d='M196 92 H514 Q548 92 548 126 V202 Q548 236 514 236 H506 L526 284 L456 236 H196 Q162 236 162 202 V126 Q162 92 196 92 Z' fill='#141413' stroke-width='5'/>
  <text x='204' y='180' font-family='Hannotate SC' font-size='42' font-weight='700' fill='#FAF9F5' stroke='none'>{q}</text>
  <g transform='translate(460 540) rotate(124)'>
    <path d='M-44 -26 C-66 -34 -76 -46 -84 -62 M-48 4 C-72 4 -84 0 -96 -8 M-42 32 C-62 44 -70 58 -76 76 M44 -26 C66 -34 76 -46 84 -62 M48 4 C72 4 84 0 96 -8 M42 32 C62 44 70 58 76 76' fill='none' stroke-width='5'/>
    <ellipse cx='0' cy='6' rx='50' ry='64' fill='#D97757' stroke-width='5.5'/><path d='M0 -54 V68' stroke-width='4' fill='none'/>
    <circle cx='-22' cy='-4' r='8' fill='#141413' stroke='none'/><circle cx='24' cy='20' r='9' fill='#141413' stroke='none'/><circle cx='-18' cy='38' r='6' fill='#141413' stroke='none'/>
    <circle cx='0' cy='-68' r='26' fill='#141413' stroke-width='5'/><circle cx='-9' cy='-76' r='5' fill='#FAF9F5' stroke='none'/><circle cx='9' cy='-76' r='5' fill='#FAF9F5' stroke='none'/>
    <path d='M-10 -90 C-20 -120 -38 -128 -52 -124 M10 -90 C20 -120 38 -128 52 -124' fill='none' stroke-width='5'/></g>
  <path d='M92 332 H450 Q488 332 488 370 V510 Q488 548 450 548 H178 L130 600 L140 548 H92 Q54 548 54 510 V370 Q54 332 92 332 Z' fill='#FAF9F5' stroke-width='5.5'/>
  <text x='94' y='404' font-family='Hannotate SC' font-size='38' font-weight='700' fill='#141413' stroke='none'>{a}</text>
  <g fill='none' stroke='#73726C' stroke-width='4.5'><path d='M96 458 C112 440 124 476 140 458 S168 440 184 458 S212 476 228 458 S256 440 272 458 S300 476 316 458 S344 440 360 458 S388 476 404 458'/>
    <path d='M96 506 C110 486 126 520 142 500 C154 484 132 478 132 496 C132 516 166 518 180 500 S212 484 228 504 C238 516 256 490 244 484 C232 480 236 510 262 508 S296 488 312 504'/></g>
  <g font-family='Hannotate SC' fill='#141413' stroke='none'><text x='238' y='668' font-size='36' font-weight='700'>{lb}</text><text x='60' y='300' font-size='30' font-weight='700'>{nt}</text></g>
  <g fill='none' stroke-width='3.5'><path d='M436 656 C466 652 488 634 496 606'/><path d='M481 614 L497 603 L505 619'/><path d='M52 312 C30 340 30 380 48 410'/><path d='M34 398 L49 412 L60 396'/></g>
  <g fill='#FAF9F5' stroke-width='3'><path data-star='84,150,18'/><path data-star='570,318,13'/><path data-star='40,620,13'/><path data-star='568,56,11'/></g>
</g></svg>"""

ILLUS = {'bottle': illus_bottle, 'doc': illus_doc, 'flag': illus_flag, 'ticket-fan': illus_ticket_fan,
         'magnifier': illus_magnifier, 'bug': illus_bug}

def illus(v):
    """v = {"name": ..., "params": {...}}  或  {"svg": "<svg ...>"}(自绘,见 design-rules.md 手绘配方)"""
    if v.get('svg'):
        return v['svg']
    if v.get('svg_file'):
        path = os.path.join(SPEC_DIR, v['svg_file'])
        if not os.path.exists(path):
            sys.exit(f'找不到 svg_file:{path}')
        return open(path, encoding='utf-8').read()
    name = v.get('name')
    if name not in ILLUS:
        sys.exit(f'未知插画 "{name}",可用:{", ".join(ILLUS)};或改用 "svg" 自绘')
    return ILLUS[name](v.get('params', {}))

# ---------------------------------------------------------------- components
def prompt_box(p, small=False):
    arg = f'<span class="arg">{esc(p["arg"])}</span>' if p.get('arg') else ''
    return (f'<div class="prompt{" sm" if small else ""}" data-fit data-autofit><span class="gt">&gt;</span>'
            f'<span class="cmd">{esc(p["cmd"])}</span>{arg}</div>')

def block(b):
    t = b['type']
    if t == 'voice':
        hs = [8, 16, 24, 12, 20, 26, 14, 8, 18, 10, 22, 12, 6, 16, 10]
        bars = ''.join(f'<i style="height:{h}px"></i>' for h in hs)
        return (f'<div class="blk voice" data-fit><div class="wave">{MIC.format(w=20, h=24)}<span class="bars">{bars}</span></div>'
                f'<p data-maxlines="{b.get("maxlines", 3)}">“{md(b["text"])}”</p></div>')
    if t == 'qa':
        items = ''.join(f'<div class="q" data-fit><i></i>{md(x["q"])}</div>' if 'q' in x else f'<div class="a" data-fit>{md(x["a"])}</div>' for x in b['items'])
        return f'<div class="blk qa" data-fit>{items}</div>'
    if t == 'log':
        items = ''.join(f'<div class="{x.get("state", "done")}" data-fit>{state_icon(x.get("state", "done"), 20)}{md(x["text"])}</div>' for x in b['items'])
        return f'<div class="blk log" data-fit>{items}</div>'
    if t == 'out':
        items = ''.join(f'<div data-fit><i></i><span>{md(x)}</span></div>' for x in b['items'])
        return f'<div class="blk out" data-fit>{items}</div>'
    if t == 'illus':
        return f'<div class="blk illus" data-fit>{illus(b)}</div>'
    sys.exit(f'未知 block 类型 "{t}"(可用 voice / qa / log / out / illus)')

def window_card(v):
    inner = ''
    if v.get('session', True):
        inner += f'<div class="newsess"><i></i>{esc(v.get("session_label", "新会话"))}</div>'
    if v.get('prompt'):
        inner += prompt_box(v['prompt'], small=v.get('stacked', False) or v.get('small_prompt', False))
    inner += ''.join(block(b) for b in v.get('blocks', []))
    if v.get('stamp'):
        inner += (f'<div class="stamp"><svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8.4l3.2 3.1L13 4.6" fill="none" '
                  f'stroke="#C15F3C" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>{esc(v["stamp"])}</div>')
    if v.get('stacked'):
        return f'<div class="vis stack"><div class="card b2"></div><div class="card b1"></div><div class="card front" data-box>{inner}</div></div>'
    return f'<div class="vis"><div class="card" data-box>{inner}</div></div>'

def issue_card(v):
    rows = v.get('rows', [])
    head_icon = state_icon(v['state'], 22) if v.get('state') else ''
    head_id = f'<span class="id">{esc(v["id"])}</span>' if v.get('id') else ''
    out = f'<div class="ihead" data-fit>{head_icon}<span>{md(v["title"])}</span>{head_id}</div>'
    if v.get('label') or v.get('progress'):
        done = sum(1 for r in rows if r.get('state') == 'done')
        pct = round(100 * done / max(len(rows), 1))
        lbl = f'<span class="lbl">{esc(v["label"])}</span>' if v.get('label') else ''
        pt = v.get('progress') or f'{done}/{len(rows)}'
        out += f'<div class="imeta" data-fit>{lbl}<span class="prog"><i style="width:{pct}%"></i></span><span class="pt">{esc(pt)}</span></div>'
    lis = ''
    id_first = v.get('id_first', False)
    for r in rows:
        rid = f'<span class="rid{"" if id_first else " end"}">{esc(r["id"])}</span>' if r.get('id') else ''
        dep = f'<span class="dep">{esc(r["dep"])}</span>' if r.get('dep') else ''
        badge = ''
        if r.get('badge'):
            bg = r['badge'] if isinstance(r['badge'], dict) else {'text': r['badge']}
            badge = f'<span class="badge {bg.get("tone", "")}">{esc(bg["text"])}</span>'
        text = f'<span class="t">{md(r["text"])}{dep}</span>'
        body = (rid + text + badge) if id_first else (text + (badge or rid))
        lis += f'<li class="{r.get("state", "todo")}" data-fit>{state_icon(r.get("state"))}{body}</li>'
    return f'<div class="vis"><div class="card issue" data-box>{out}<ul>{lis}</ul></div></div>'


def diff_card(v):
    stat = v.get('stat', {})
    st = ''.join(f'<i class="{k}">{esc(stat[k])}</i>' for k in ('add', 'del') if stat.get(k))
    out = f'<div class="dhead" data-fit><span>{md(v.get("title", "Files changed"))}</span><span class="stat">{st}</span></div><div class="dbody">'
    for f in v.get('files', []):
        tag = f'<span class="dtag">{esc(f["tag"])}</span>' if f.get('tag') else ''
        out += f'<div class="dfile" data-fit><span class="fn">{esc(f["file"])}</span>{tag}</div>'
        for ln in f.get('lines', []):
            sign = ln.get('sign', ' ')
            cls = {'+': 'add', '-': 'del', '−': 'del'}.get(sign, 'ctx')
            out += f'<div class="dline {cls}" data-fit><b>{esc(sign)}</b><code>{esc(ln["code"])}</code></div>'
    if v.get('more'):
        out += f'<div class="dmore">{esc(v["more"])}</div>'
    out += '</div>'  # 关 dbody
    return f'<div class="vis"><div class="card diff" data-box>{out}</div></div>'

def station_visual(v):
    t = v['type']
    if t == 'window':
        return window_card(v)
    if t == 'issue':
        return issue_card(v)
    if t == 'diff':
        return diff_card(v)
    if t in ('illus', 'svg'):
        return f'<div class="vis">{illus(v)}</div>'
    sys.exit(f'未知 station 视觉类型 "{t}"(可用 window / issue / diff / illus / svg)')

DEFAULT_W = {'window': 300, 'issue': 420, 'diff': 480, 'illus': 224, 'svg': 224}

def label_html(lab):
    if not lab:
        return ''
    if lab.get('num') is not None:
        mark = f'<span class="num">{esc(lab["num"])}</span>'
    elif lab.get('icon'):
        style, svg = LABEL_ICONS[lab['icon']]
        mark = f'<span class="ico {style}">{svg}</span>'
    else:
        mark = ''
    return f'<div class="lab" data-fit>{mark}<span>{md(lab["text"])}</span></div>'

# ---------------------------------------------------------------- slide types
def topbar(spec, i, n):
    page = f'<span class="page"><b>{i:02d}</b> / {n:02d}</span>' if spec.get('page_numbers', True) else '<span></span>'
    return f'<header class="topbar"><span class="kicker">{esc(spec.get("kicker", ""))}</span>{page}</header>'

def headed(s):
    out = f'<h2 data-maxlines="{s.get("headline_lines", 1)}" style="{hsize(s)}">{md(s["headline"], head=True)}</h2>'
    tag, sub = s.get('tag'), s.get('subtitle')
    if tag or sub:
        t = ''
        if tag:
            tg = tag if isinstance(tag, dict) else {'text': tag}
            t = f'<span class="tag {tg.get("style", "")}">{esc(tg["text"])}</span>'
        out += f'<div class="subt" data-maxlines="1">{t}<span>{md(sub or "")}</span></div>'
    return out

def hsize(s):
    return f'font-size:{s["headline_size"]}px' if s.get('headline_size') else ''

def slide_split(s):
    art = s.get('art')
    art_w = art.get('width', 760 if art and art.get('type') == 'terminal' else 600) if art else 0
    left_w = INNER_W - art_w - 56 if art else INNER_W
    h = f'<h1 data-maxlines="{s.get("headline_lines", 2)}" style="{hsize(s)}">{md(s["headline"], head=True)}</h1>'
    if s.get('sub'):
        h += f'<p class="sub" data-maxlines="{s.get("sub_lines", 2)}">{md(s["sub"])}</p>'
    if s.get('paras'):
        ps = ''.join(f'<p data-maxlines="{p.get("maxlines", 2)}">{"<b>" + md(p["lead"]) + "</b>" if p.get("lead") else ""}{md(p["text"])}</p>' for p in s['paras'])
        h += f'<div class="paras">{ps}</div>'
    bottom = ''
    if s.get('list'):
        items = ''.join(f'<div data-fit><span class="n">{i + 1:02d}</span><p>{md(x)}</p></div>' for i, x in enumerate(s['list']))
        bottom += f'<div class="list">{items}</div>'
    if s.get('answer'):
        a = s['answer']
        toks = []
        for tk in a['tokens']:
            tk = tk if isinstance(tk, dict) else {'text': tk}
            toks.append(f'<span class="{"cmd" if tk.get("cmd", tk["text"].startswith("/")) else ""}">{esc(tk["text"])}</span>')
        pill = '<span class="plus">+</span>'.join(toks)
        lbl = f'<span class="lbl">{esc(a["label"])}</span>' if a.get('label') else ''
        bottom += f'<div class="answer">{lbl}<span class="pill" data-autofit>{pill}</span></div>'
    if bottom:
        h += f'<div class="bottom">{bottom}</div>'
    body = f'<div class="left" style="width:{left_w}px" data-box>{h}</div>'
    if art:
        bg = color(art.get('color'), 'clay')
        if art.get('type') == 'terminal':
            inner = terminal(art)
        else:
            inner = illus(art)
        body += f'<div class="art" style="width:{art_w}px;background:{bg}">{inner}</div>'
    return body

def terminal(t):
    rows = ''
    for ln in t.get('lines', []):
        k = ln['type']
        if k == 'prompt':
            arg = f'&nbsp;{esc(ln["arg"])}' if ln.get('arg') else ''
            rows += f'<div class="ln dim" data-fit>&gt;&nbsp;<span class="c">{esc(ln["cmd"])}</span>{arg}</div>'
        elif k == 'gap':
            rows += '<div class="gap"></div>'
        elif k == 'ai':
            chip = f'<span class="chip">{esc(ln["chip"])}</span>' if ln.get('chip') else ''
            rows += f'<div class="ln" data-fit><span class="dot"></span>{chip}{md(ln["text"])}</div>'
            rows += ''.join(f'<div class="ln ind" data-fit>{md(c)}</div>' for c in ln.get('cont', []))
        elif k == 'options':
            opts = ''
            for i, o in enumerate(ln['items']):
                rec = f'<span class="rec">{esc(o["rec"])}</span>' if o.get('rec') else ''
                pre = '❯' if o.get('on') else '&nbsp;'
                opts += f'<div class="opt{" on" if o.get("on") else ""}" data-fit>{pre} {i + 1}. {md(o["text"])}{rec}</div>'
            rows += f'<div class="opts">{opts}</div>'
        elif k == 'user':
            rows += f'<div class="user" data-fit><span class="dim">&gt;</span>{md(ln["text"])}</div>'
        elif k == 'spinner':
            rows += f'<div class="ln spin" data-fit>✻&nbsp;{md(ln["text"])}</div>'
        else:
            sys.exit(f'未知终端行类型 "{k}"(可用 prompt / gap / ai / options / user / spinner)')
    inp = t.get('input')
    inp_html = ''
    if inp is not False:
        inp = inp or {}
        hint = f'<span class="hint">{esc(inp["hint"])}</span>' if inp.get('hint') else ''
        mic = MIC.format(w=26, h=30) if inp.get('mic', True) else ''
        inp_html = f'<div class="input"><span class="dim">&gt;</span><span class="cursor"></span>{hint}{mic}</div>'
    title = esc(t.get('title', '~/my-app — claude'))
    return (f'<div class="term" data-box><div class="chrome"><i></i><i></i><i></i><span>{title}</span></div>'
            f'<div class="tb">{rows}</div>{inp_html}</div>')

def slide_flow(s):
    sts = s['stations']
    gap = 60
    ws = [st.get('w', DEFAULT_W[st['visual']['type']]) for st in sts]
    total = sum(ws) + gap * (len(sts) - 1)
    # 站点少时别把卡片拉得太宽:最多放大 1.3 倍,剩余空间两侧均分(整体居中)
    k = min(INNER_W / total, 1.3)
    ws = [round(w * k) for w in ws]
    span = sum(ws) + gap * (len(sts) - 1)
    if k == INNER_W / total:
        ws[-1] += INNER_W - span
        span = INNER_W
    out, x = '', (INNER_W - span) // 2
    for i, (st, w) in enumerate(zip(sts, ws)):
        cap = f'<div class="cap" data-maxlines="{st.get("cap_lines", 2)}">{md(st["caption"])}</div>' if st.get('caption') else ''
        out += f'<div class="st" style="left:{x}px;width:{w}px" data-box>{station_visual(st["visual"])}{label_html(st.get("label"))}{cap}</div>'
        x += w
        if i < len(sts) - 1:
            out += ARROW.format(x=x)
            x += gap
    return headed(s) + f'<div class="flow">{out}</div>'

def slide_compare(s):
    cols = ''
    for c in s['columns']:
        tag = ''
        if c.get('tag'):
            tg = c['tag'] if isinstance(c['tag'], dict) else {'text': c['tag']}
            tag = f'<span class="tag ctag {tg.get("style", "")}">{esc(tg["text"])}</span>'
        rows = ''.join(f'<div class="row" data-fit><span class="n">{i + 1:02d}</span><p data-maxlines="{c.get("item_lines", 1)}">{md(x)}</p></div>'
                       for i, x in enumerate(c.get('items', [])))
        tone = c.get('color', 'ivory')
        cls = 'col' + (' dark' if tone == 'dark' else '') + (' muted' if c.get('muted') else '')
        bg = '' if tone == 'dark' else f'background:{color(tone, "ivory")}'
        cols += (f'<div class="{cls}" style="{bg}" data-box>{tag}<h3 data-maxlines="{c.get("title_lines", 1)}">{md(c["title"], head=True)}</h3>'
                 f'<div class="rows">{rows}</div></div>')
    ratio = s.get('ratio') or [1] * len(s['columns'])
    tpl = ' '.join(f'{r}fr' for r in ratio)
    return headed(s) + f'<div class="cols" style="grid-template-columns:{tpl}">{cols}</div>'

def slide_custom(s):
    return (headed(s) if s.get('headline') else '') + s['html']

SLIDES = {'split': slide_split, 'flow': slide_flow, 'compare': slide_compare, 'custom': slide_custom}

# ---------------------------------------------------------------- page + lint
PAGE_JS = r'''
function star(cx,cy,r){const k=.28*r,t=.1*r;return `M${cx},${cy-r} C${cx+t},${cy-k} ${cx+k},${cy-t} ${cx+r},${cy} C${cx+k},${cy+t} ${cx+t},${cy+k} ${cx},${cy+r} C${cx-t},${cy+k} ${cx-k},${cy+t} ${cx-r},${cy} C${cx-k},${cy-t} ${cx-t},${cy-k} ${cx},${cy-r}Z`}
document.querySelectorAll('[data-star]').forEach(el=>{const [x,y,r]=el.dataset.star.split(',').map(Number);el.setAttribute('d',star(x,y,r))});
const notes=[];const desc=el=>(el.innerText||el.textContent||'').replace(/\s+/g,' ').trim().slice(0,36);
document.querySelectorAll('[data-autofit]').forEach(el=>{let fs=parseFloat(getComputedStyle(el).fontSize),f0=fs;
  while(el.scrollWidth>el.clientWidth+1&&fs>14){fs-=1;el.style.fontSize=fs+'px'}
  if(fs<f0)notes.push({level:'info',msg:`放不下,自动缩字 ${f0}→${fs}px`,el:desc(el)})});
function lines(el){const r=document.createRange();r.selectNodeContents(el);const L=[];
  [...r.getClientRects()].filter(x=>x.width>.5&&x.height>.5).forEach(x=>{const t=L.find(l=>Math.abs(l.mid-(x.top+x.height/2))<x.height*.45);
    if(t){t.l=Math.min(t.l,x.left);t.r=Math.max(t.r,x.right)}else L.push({mid:x.top+x.height/2,l:x.left,r:x.right})});return L.sort((a,b)=>a.mid-b.mid)}
document.querySelectorAll('[data-maxlines]').forEach(el=>{const L=lines(el),max=+el.dataset.maxlines,fs=parseFloat(getComputedStyle(el).fontSize);
  if(L.length>max)notes.push({level:'warn',msg:`折成 ${L.length} 行,上限 ${max} 行`,el:desc(el)});
  if(L.length>1){const last=L[L.length-1];if(last.r-last.l<fs*2.6)notes.push({level:'warn',msg:'末行只剩一两个字(孤字),改措辞或手动 \\n 断行',el:desc(el)})}});
document.querySelectorAll('[data-fit]').forEach(el=>{const box=el.parentElement&&el.parentElement.closest('[data-box]');if(!box)return;
  const a=el.getBoundingClientRect(),b=box.getBoundingClientRect();
  if(a.right>b.right+1.5||a.bottom>b.bottom+1.5||a.left<b.left-1.5)notes.push({level:'warn',msg:'超出所在卡片/栏',el:desc(el)});
  else if(el.scrollWidth>el.clientWidth+1)notes.push({level:'warn',msg:getComputedStyle(el).overflow==='visible'?'文字伸出了所在行/卡片':'内容被截断',el:desc(el)})});
const S=document.querySelector('.slide').getBoundingClientRect();
document.querySelectorAll('.slide [data-box], .slide .arr').forEach(el=>{const a=el.getBoundingClientRect();
  if(a.right>S.right+1||a.bottom>S.bottom+1||a.left<S.left-1||a.top<S.top-1)notes.push({level:'warn',msg:'超出画布(可能是 HTML 没闭合或宽度算错)',el:desc(el)||el.className})});
const o=document.createElement('script');o.type='application/json';o.id='lint-out';o.textContent=JSON.stringify(notes);document.body.appendChild(o);
'''

def page(spec, s, i, n):
    kind = s.get('type', 'split')
    if kind not in SLIDES:
        sys.exit(f'第 {i} 张:未知版式 "{kind}"(可用 {", ".join(SLIDES)})')
    cls = 't-' + kind + (' headed' if kind in ('flow', 'compare', 'custom') else '')
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{i:02d}</title>'
            f'<link rel="stylesheet" href="file://{CSS}"></head><body><div class="slide {cls}" data-box>{DEFS}'
            f'{topbar(spec, i, n)}{SLIDES[kind](s)}</div><script>{PAGE_JS}</script></body></html>')

def chrome(args):
    if not os.path.exists(CHROME):
        sys.exit(f'找不到 Chrome:{CHROME}(可用环境变量 CHROME 指定)')
    return subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                           '--virtual-time-budget=1500', *args], capture_output=True, text=True)

def shoot(html_path, png, scale, w=1600, h=900):
    chrome([f'--force-device-scale-factor={scale}', f'--window-size={w},{h}', f'--screenshot={png}', 'file://' + html_path])
    if not os.path.exists(png):
        sys.exit(f'出图失败:{png}')

def lint(html_path):
    r = chrome(['--window-size=1600,900', '--dump-dom', 'file://' + html_path])
    m = re.search(r'<script type="application/json" id="lint-out">(.*?)</script>', r.stdout, re.S)
    return json.loads(H.unescape(m.group(1))) if m else [{'level': 'warn', 'msg': '体检脚本没跑出结果', 'el': ''}]

def grid(pngs, out):
    n = len(pngs)
    rows = math.ceil(n / 2) if n > 1 else 1
    cols = 2 if n > 1 else 1
    w, h = 1600, int(900 * rows / (2 if cols == 2 else 1))
    imgs = ''.join(f'<img src="file://{p}">' for p in pngs)
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;width:{w}px;height:{h}px;background:#fff}}'
           f'.g{{display:grid;grid-template-columns:repeat({cols},1fr);grid-template-rows:repeat({rows},1fr);gap:4px;width:{w}px;height:{h}px}}'
           f'img{{width:100%;height:100%;min-height:0;object-fit:cover;display:block}}</style></head><body><div class="g">{imgs}</div></body></html>')
    gp = out[:-4] + '.html'
    open(gp, 'w', encoding='utf-8').write(doc)
    shoot(gp, out, 1, w, h)
    os.remove(gp)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--final', action='store_true', help='2x 定稿,输出到下一个 vN/')
    ap.add_argument('--only', help='只出这几张,如 2,4(从 1 数)')
    a = ap.parse_args()
    spec_path = os.path.abspath(a.spec)
    spec = json.load(open(spec_path, encoding='utf-8'))
    root = os.path.dirname(spec_path)
    global SPEC_DIR
    SPEC_DIR = root
    slides = spec['slides']
    n = len(slides)
    only = {int(x) for x in a.only.split(',')} if a.only else set(range(1, n + 1))

    if a.final:
        vs = [int(m.group(1)) for d in os.listdir(root) if (m := re.fullmatch(r'v(\d+)', d))]
        out = os.path.join(root, f'v{max(vs, default=0) + 1}')
        scale = 2
    else:
        out = os.path.join(root, 'preview')
        scale = 1
    build = os.path.join(root, '.build')
    os.makedirs(out, exist_ok=True)
    os.makedirs(build, exist_ok=True)

    warn_total = 0
    for i, s in enumerate(slides, 1):
        if i not in only:
            continue
        hp = os.path.join(build, f'{i:02d}.html')
        open(hp, 'w', encoding='utf-8').write(page(spec, s, i, n))
        png = os.path.join(out, f'{i:02d}.png')
        shoot(hp, png, scale)
        notes = lint(hp)
        warns = [x for x in notes if x['level'] == 'warn']
        warn_total += len(warns)
        print(f'[{i:02d}] {png}  ' + ('✓ 体检通过' if not warns else f'⚠ {len(warns)} 处问题'))
        for x in notes:
            print(f'     {"⚠" if x["level"] == "warn" else "·"} {x["msg"]}:「{x["el"]}」')

    pngs = [os.path.join(out, f'{i:02d}.png') for i in range(1, n + 1) if os.path.exists(os.path.join(out, f'{i:02d}.png'))]
    gp = os.path.join(out, 'grid.png')
    grid(pngs, gp)
    print(f'[grid] {gp}')
    if a.final:
        shutil.copy(spec_path, os.path.join(out, 'spec.json'))
    print(f'共 {warn_total} 处待修' if warn_total else '全部通过')

if __name__ == '__main__':
    main()
