"""releases.json → 静的 index.html(T-201〜T-204)。

決定論: 出力は入力 JSON のみで決まる(時刻は generated_at 由来、乱数なし)。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape

_JST = timezone(timedelta(hours=9))


def _jst(iso_utc: str) -> str:
    dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00")).astimezone(_JST)
    return dt.strftime("%Y-%m-%d %H:%M")


def _date_label(date: str) -> str:
    return date if date else "—"


def _company_section(co: dict) -> str:
    rows = []
    for it in co["items"]:
        rows.append(
            f'      <li><span class="date">{escape(_date_label(it["date"]))}</span>'
            f'<a href="{escape(it["url"], quote=True)}" class="headline"'
            f' target="_blank" rel="noopener noreferrer">{escape(it["title"])}</a></li>'
        )
    if not rows:
        rows.append('      <li class="empty">リリースを取得できていません</li>')
    note = ""
    if not co["ok"]:
        note = (
            f'    <p class="stale">直近の取得失敗(前回分を表示 / '
            f"{escape(_jst(co['fetched_at']))} JST 時点)</p>\n"
        )
    return (
        f'  <section class="company" id="{escape(co["id"])}">\n'
        f'    <h2><a href="{escape(co["source_url"], quote=True)}"'
        f' target="_blank" rel="noopener noreferrer">{escape(co["name"])}</a></h2>\n'
        f"{note}"
        f"    <ul>\n" + "\n".join(rows) + "\n    </ul>\n"
        f"  </section>"
    )


def render_html(data: dict) -> str:
    generated = _jst(data["generated_at"])
    sections = "\n".join(_company_section(co) for co in data["companies"])
    n = len(data["companies"])
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>霞が関レンズ — 中央省庁 報道発表一覧</title>
<meta name="description" content="日本の中央省庁等{n}機関の最新報道発表を5件ずつ一望">
<style>
:root {{
  --bg: #f6f5f1; --card: #ffffff; --ink: #1f2328; --sub: #6a6f76;
  --line: #e3e1da; --accent: #5b3a8e; --stale: #a15c07;
}}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #14171a; --card: #1d2126; --ink: #e6e4de; --sub: #9aa0a6;
    --line: #2c3138; --accent: #b39ddb; --stale: #e0a94e; }}
}}
* {{ box-sizing: border-box; margin: 0; }}
body {{ background: var(--bg); color: var(--ink);
  font-family: "Hiragino Kaku Gothic ProN", "Noto Sans JP", "Yu Gothic UI", Meiryo, sans-serif;
  line-height: 1.6; padding: 2rem 1rem 3rem; }}
header, footer, main {{ max-width: 72rem; margin: 0 auto; }}
h1 {{ font-size: 1.6rem; letter-spacing: .04em; }}
h1 .en {{ font-size: .8rem; color: var(--sub); margin-left: .6em; letter-spacing: .12em; }}
.updated {{ color: var(--sub); font-size: .85rem; margin: .3rem 0 1.6rem; }}
main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(21rem, 1fr)); gap: 1rem; }}
.company {{ background: var(--card); border: 1px solid var(--line); border-radius: .6rem;
  padding: 1rem 1.1rem; }}
.company h2 {{ font-size: 1.02rem; border-bottom: 2px solid var(--accent);
  padding-bottom: .45rem; margin-bottom: .6rem; }}
.company h2 a {{ color: var(--ink); text-decoration: none; }}
.company h2 a:hover {{ color: var(--accent); }}
.company ul {{ list-style: none; padding: 0; }}
.company li {{ padding: .45rem 0; border-top: 1px dashed var(--line); }}
.company li:first-child {{ border-top: none; }}
.date {{ display: block; font-size: .75rem; color: var(--sub); font-variant-numeric: tabular-nums; }}
.headline {{ color: var(--accent); text-decoration: none; font-size: .92rem; }}
.headline:hover {{ text-decoration: underline; }}
.stale {{ color: var(--stale); font-size: .78rem; margin-bottom: .4rem; }}
.empty {{ color: var(--sub); font-size: .85rem; }}
footer {{ margin-top: 2.2rem; color: var(--sub); font-size: .78rem;
  border-top: 1px solid var(--line); padding-top: 1rem; }}
footer a {{ color: var(--sub); }}
</style>
</head>
<body>
<header>
  <h1>霞が関レンズ<span class="en">KASUMIGASEKI LENS</span></h1>
  <p class="updated">中央省庁等 {n} 機関の最新報道発表(各 5 件) — 最終更新 {generated} JST(6 時間ごとに自動更新)</p>
</header>
<main>
{sections}
</main>
<footer>
  <p>本サイトは各機関が公式に公開する報道発表の見出しとリンクのみを収集・表示しています(本文は保存していません)。
  出典は各機関名のリンク先(公式サイト)をご覧ください。各発表の利用条件は出典サイトの利用規約(政府標準利用規約等)に従います。</p>
  <p><a href="https://github.com/twill3c/kasumigaseki-lens/blob/main/LICENSE" target="_blank" rel="noopener">MIT License</a> © 2026 坂田哲朗
  ・ <a href="https://github.com/twill3c/kasumigaseki-lens" target="_blank" rel="noopener">GitHub</a>
  ・ <a href="https://claude.ai/code/artifact/33922a13-af7b-44a2-8a2c-82473d122438" target="_blank" rel="noopener">kasumigaseki-lens の歩き方</a>
  ・ <a href="https://claude.ai/code/artifact/a4ead9df-d42b-41d8-99ec-cb5bc3bddbaf" target="_blank" rel="noopener">kasumigaseki-lens 設計図</a>
  ・ <a href="https://app-menu-amber.vercel.app" target="_blank" rel="noopener">App Menu</a></p>
</footer>
</body>
</html>
"""
