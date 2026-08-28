"""機関別の取得・抽出(F-01/F-06)。

fetch_company(company, get) -> [{"title","url","date"}...](新しい順)
fetch_company_full(company, get) -> {"items": [...], "source_url": str}
  source_url は取得時に解決した一覧ページ URL(空文字なら宣言値を使う)。
get(url, ua) -> bytes は注入可能(テストではフィクスチャ、実運用では http_get)。

HTML 抽出は「状態を持つ走査」で行う: 日付見出し(年月見出し・日付ラベル)と
項目リンクを 1 本の正規表現交互スキャンで拾い、直前の日付を項目に割り当てる。
構造変更で 0 件になった場合は pipeline 側で ok=False として前回分を保持する
(F-05)ため、ここでは例外にしない。
"""

from __future__ import annotations

import re
from html import unescape

from .dates import normalize_date
from .feedparse import parse_feed
from .sources import BROWSER_UA, PROJECT_UA
from .urlutil import absolutize


def _clean(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _https(url: str) -> str:
    return "https://" + url[len("http://") :] if url.startswith("http://") else url


# ---- HTML パーサ(機関別) ----------------------------------------------


def parse_maff(html: str, base: str) -> list[dict]:
    # <h2>令和8年8月分</h2> → 年の文脈 / <p class="list_item_date">8月19日</p> → 日付
    # <dl class="list_item">…<dd><a href="./…">タイトル</a></dd></dl> → 項目
    pat = re.compile(
        r"<h2>令和(\d+)年(\d{1,2})月分</h2>"
        r'|<p class="list_item_date">(\d{1,2})月(\d{1,2})日</p>'
        r'|<dl class="list_item">.*?<dd><a href="([^"]+)">(.*?)</a>',
        re.S,
    )
    items, year, date = [], None, ""
    for m in pat.finditer(html):
        if m.group(1):
            year = 2018 + int(m.group(1))
        elif m.group(3):
            if year is not None:
                date = f"{year:04d}-{int(m.group(3)):02d}-{int(m.group(4)):02d}"
        elif m.group(5) and date:
            items.append(
                {"title": _clean(m.group(6)), "url": absolutize(base, m.group(5)), "date": date}
            )
    return items


def parse_env(html: str, base: str) -> list[dict]:
    # <span class="p-press-release-list__heading">2026年08月19日発表</span> → 日付
    # <a href="/press/…" class="c-news-link__link">タイトル</a> → 項目
    pat = re.compile(
        r'class="p-press-release-list__heading">([^<]+)</span>'
        r'|<a href="(/press/[^"]+)" class="c-news-link__link">(.*?)</a>',
        re.S,
    )
    items, date = [], ""
    for m in pat.finditer(html):
        if m.group(1):
            date = normalize_date(m.group(1))
        elif m.group(2) and date:
            items.append(
                {"title": _clean(m.group(3)), "url": absolutize(base, m.group(2)), "date": date}
            )
    return items


def parse_moj_year_page(html: str, base: str) -> list[dict]:
    # 日付は <!-- dt>平成38年8月7日</dt --> のコメント内(元号継続換算は dates.py)
    pat = re.compile(
        r"<!--\s*dt>([^<]+)</dt\s*-->\s*<dd><a href=\"([^\"]+)\">(.*?)</a>", re.S
    )
    return [
        {
            "title": _clean(title),
            "url": absolutize(base, href),
            "date": normalize_date(date),
        }
        for date, href, title in pat.findall(html)
    ]


def fetch_moj(company, get, ua) -> list[dict]:
    """一覧ハブ → 最新年ページの二段取得(年ページ URL は毎年変わる)。"""
    hub_url = company["primary_url"]
    hub = get(hub_url, ua).decode("utf-8", "ignore")
    m = re.search(r'href="(/hisho/kouhou/press_r\d+[^"]*\.html)"', hub)
    if not m:
        return []
    year_url = absolutize(hub_url, m.group(1))
    return parse_moj_year_page(get(year_url, ua).decode("utf-8", "ignore"), year_url)


def parse_mofa(html: str, base: str) -> list[dict]:
    # 年は本文の「令和N年」から。<dt class="list-title">8月19日付</dt> → 日付
    # <a href="/mofaj/press/release/…">タイトル</a> → 項目
    era = re.search(r"令和(\d+)年", html)
    year = 2018 + int(era.group(1)) if era else None
    pat = re.compile(
        r'<dt class="list-title">(\d{1,2})月(\d{1,2})日付</dt>'
        r'|<a href="(/mofaj/press/release/[^"]+)">(.*?)</a>',
        re.S,
    )
    items, date = [], ""
    for m in pat.finditer(html):
        if m.group(1):
            if year is not None:
                date = f"{year:04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        elif m.group(3) and date:
            items.append(
                {"title": _clean(m.group(4)), "url": absolutize(base, m.group(3)), "date": date}
            )
    return items


def parse_meti(html: str, base: str) -> list[dict]:
    # <div class="left txt_box"><p>2026年8月17日</p>
    # <a class="cut_txt" href="/press/2026/08/20260817001.html">タイトル</a>
    pat = re.compile(
        r'<div class="left txt_box"><p>([^<]+)</p>\s*'
        r'<a class="cut_txt" href="([^"]+)">(.*?)</a>',
        re.S,
    )
    return [
        {
            "title": _clean(title),
            "url": absolutize(base, href),
            "date": normalize_date(date),
        }
        for date, href, title in pat.findall(html)
    ]


# ---- 首相官邸(系統別カード) --------------------------------------------
#
# 一覧のマークアップは 3 種類(2026-08-29 実測):
#   list-photo    総理の一日(actions)・総理の演説・記者会見など(statement)
#   list-standard 総理の指示・談話など(discourse)
#   list-press    内閣官房長官記者会見(tyoukanpress、日付見出し + 午前/午後)


def parse_kantei_photo_list(html: str, base: str) -> list[dict]:
    pat = re.compile(
        r'<a class="list-photo__link" href="([^"]+)".*?'
        r'<p class="list-photo__title">(.*?)</p>\s*'
        r'<p class="list-photo__date">([^<]+)</p>',
        re.S,
    )
    return [
        {
            "title": _clean(title),
            "url": absolutize(base, href),
            "date": normalize_date(date),
        }
        for href, title, date in pat.findall(html)
    ]


def parse_kantei_standard_list(html: str, base: str) -> list[dict]:
    pat = re.compile(
        r'<a class="list-standard__link" href="([^"]+)">\s*'
        r'<p class="list-standard__date">([^<]+)</p>\s*'
        r'<p class="list-standard__description">(.*?)</p>',
        re.S,
    )
    return [
        {
            "title": _clean(title),
            "url": absolutize(base, href),
            "date": normalize_date(date),
        }
        for href, date, title in pat.findall(html)
    ]


def parse_kantei_press_list(html: str, base: str) -> list[dict]:
    # 日付は <h3> 見出し、項目は午前/午後ラベル + 発言要旨。
    # 「冒頭発言なし」が連日並ぶため、ラベルを見出しに含めないと区別がつかない。
    pat = re.compile(
        r'<h3 class="list-press__date">([^<]+)</h3>'
        r'|<a class="list-press__link" href="([^"]+)">\s*'
        r'<span class="label[^"]*">([^<]*)</span>\s*'
        r'<span class="list-press__description">(.*?)</span>',
        re.S,
    )
    items, date = [], ""
    for m in pat.finditer(html):
        if m.group(1):
            date = normalize_date(m.group(1))
        elif m.group(2) and date:
            label, body = _clean(m.group(3)), _clean(m.group(4))
            items.append(
                {
                    "title": f"{label} {body}".strip(),
                    "url": absolutize(base, m.group(2)),
                    "date": date,
                }
            )
    return items


_KANTEI_SECTION_PARSERS = {
    "actions": parse_kantei_photo_list,
    "statement": parse_kantei_photo_list,
    "discourse": parse_kantei_standard_list,
}


def resolve_kantei_section(hub_html: str, base: str, section: str) -> str:
    """トップページ(hub)から現行の代番号を解決し、系統一覧の URL を返す。

    官邸のセクションは /jp/{代}/{section}/index.html。代番号は総理交代で
    上がるため決め打ちしない。複数見つかったら最大(=最新)を採る。
    見つからなければ空文字(呼び出し側で 0 件 → ok=False に落ちる)。
    """
    nums = [int(n) for n in re.findall(rf"/jp/(\d+)/{section}/index\.html", hub_html)]
    if not nums:
        return ""
    return absolutize(base, f"/jp/{max(nums)}/{section}/index.html")


def fetch_kantei_sections(company, get, ua) -> dict:
    """hub → 系統一覧の二段取得。複数系統は結合して日付降順に並べる。

    どれか 1 系統でも 0 件なら全体を 0 件として返す(部分欠落を「取得成功」に
    見せない — 経産省フィード凍結の教訓)。
    """
    hub_url = company["primary_url"]
    hub = get(hub_url, ua).decode("utf-8", "ignore")
    merged: list[dict] = []
    first_url = ""
    for section in company["kantei_sections"]:
        url = resolve_kantei_section(hub, hub_url, section)
        if not url:
            return {"items": [], "source_url": ""}
        items = _KANTEI_SECTION_PARSERS[section](
            get(url, ua).decode("utf-8", "ignore"), url
        )
        if not items:
            return {"items": [], "source_url": ""}
        first_url = first_url or url
        merged.extend(items)
    merged.sort(key=lambda it: it["date"], reverse=True)  # 安定ソート(同日は宣言順)
    return {"items": merged, "source_url": first_url}


_HTML_PARSERS = {
    "maff": parse_maff,
    "env": parse_env,
    "mofa": parse_mofa,
    "meti": parse_meti,
    "kantei_tyoukanpress": parse_kantei_press_list,
}


# ---- 入口 ----------------------------------------------------------------


def fetch_company_full(company, get) -> dict:
    """items と、実際に参照した一覧ページ URL を返す。

    source_url が空文字なら「宣言値をそのまま使う」の意(pipeline 側で解釈)。
    官邸の系統別カードだけは代番号が動くため、解決済み URL を返す。
    """
    ua = BROWSER_UA if company.get("ua") == "browser" else PROJECT_UA
    strategy = company["strategy"]
    source_url = ""
    if company.get("kantei_sections"):
        resolved = fetch_kantei_sections(company, get, ua)
        items, source_url = resolved["items"], resolved["source_url"]
    elif strategy == "feed":
        items = parse_feed(get(company["primary_url"], ua))
        base = company["primary_url"]
        items = [
            {**it, "url": absolutize(base, it["url"])} for it in items
        ]
        pf = company.get("path_filter")
        if pf:
            items = [it for it in items if pf in it["url"]]
    elif company["id"] == "moj":
        items = fetch_moj(company, get, ua)
    else:
        html = get(company["primary_url"], ua).decode("utf-8", "ignore")
        items = _HTML_PARSERS[company["id"]](html, company["primary_url"])
    return {
        "items": [
            {"title": it["title"], "url": _https(it["url"]), "date": it["date"]}
            for it in items
            if it["title"] and it["url"]
        ],
        "source_url": _https(source_url) if source_url else "",
    }


def fetch_company(company, get) -> list[dict]:
    return fetch_company_full(company, get)["items"]
