# T-006〜T-010: 首相官邸の系統別カード(代番号解決・ラベル・束ね・source_url 上書き)
#
# 期待値の出所: 2026-08-29 に実サイトから保存した tests/fixtures/kantei_*.html
#(tools/refetch_fixtures.py)。合成 HTML を使うケースは、実物のマークアップを
# 削り出したもので、実フィクスチャ側の対照ケースと対にしてある。
import json
from pathlib import Path

import pytest

from src.fetchers import (
    fetch_company_full,
    parse_kantei_press_list,
    resolve_kantei_section,
)
from src.pipeline import collect
from src.sources import COMPANIES

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent / "fixtures"


def company(cid):
    return next(c for c in COMPANIES if c["id"] == cid)


def fixture_get(co):
    ext = "xml" if co["strategy"] == "feed" else "html"
    mapping = {co["primary_url"]: FIX / f"{co['id']}.{ext}"}
    map_json = FIX / "pages" / co["id"] / "map.json"
    if map_json.exists():
        for url, fname in json.loads(map_json.read_text(encoding="utf-8")).items():
            mapping[url] = FIX / "pages" / co["id"] / fname

    def get(url, ua):
        if url not in mapping:
            raise AssertionError(f"フィクスチャに無い URL への fetch: {url}")
        return mapping[url].read_bytes()

    return get


# ---- T-006: 代番号の解決(総理交代で /jp/{代}/ が動く) --------------------

HUB_BASE = "https://www.kantei.go.jp/index.html"


def test_t006_resolves_highest_generation():
    # 旧代へのリンク(沿革・アーカイブ)が残っていても最新代を採る
    hub = (
        '<a href="/jp/104/actions/index.html">前内閣</a>'
        '<a href="/jp/105/actions/index.html">総理の一日</a>'
    )
    assert (
        resolve_kantei_section(hub, HUB_BASE, "actions")
        == "https://www.kantei.go.jp/jp/105/actions/index.html"
    )


def test_t006_returns_empty_when_absent():
    # 陰性対照: 該当セクションが無い hub では空文字(例外にしない)
    hub = '<a href="/jp/tyoukanpress/index.html">官房長官会見</a>'
    assert resolve_kantei_section(hub, HUB_BASE, "actions") == ""


def test_t006_does_not_match_other_sections():
    # 陽性対照の対: statement を探して discourse を拾ってはいけない
    hub = '<a href="/jp/105/discourse/index.html">指示・談話</a>'
    assert resolve_kantei_section(hub, HUB_BASE, "statement") == ""
    assert (
        resolve_kantei_section(hub, HUB_BASE, "discourse")
        == "https://www.kantei.go.jp/jp/105/discourse/index.html"
    )


@pytest.mark.parametrize(
    "cid,section", [("kantei_actions", "actions"), ("kantei_statement", "statement")]
)
def test_t006_declared_source_url_matches_live_hub(cid, section):
    # 実フィクスチャの hub から解決した URL が sources.py の宣言値と一致する
    # (総理交代で宣言値だけが取り残されるドリフトを検出する)
    co = company(cid)
    hub = (FIX / f"{cid}.html").read_text("utf-8", "ignore")
    assert resolve_kantei_section(hub, co["primary_url"], section) == co["source_url"]


# ---- T-007: 官房長官会見は午前/午後ラベルを見出しに含める ------------------


def test_t007_press_list_keeps_ampm_label():
    co = company("kantei_tyoukanpress")
    items = fetch_company_full(co, fixture_get(co))["items"]
    assert items, "官房長官会見が 0 件"
    assert all(it["title"].startswith(("午前", "午後")) for it in items[:10])
    # 実測(2026-08-29): 「冒頭発言なし」だけの日が連続するのでラベルは必要。
    # ただし (日付, 見出し) は一意ではない — 同日午後に同題の会見が 2 回ある例が
    # 実在する(2026-07-28 の 28_p2 / 28_p3)。一意なのは URL のみ。
    urls = [it["url"] for it in items]
    assert len(urls) == len(set(urls))
    # ラベルを落とすと見出しが潰れることの陽性対照(同日・午前/午後の同題)
    same_day = [it["title"] for it in items if it["date"] == "2026-07-23"]
    assert same_day and len(set(same_day)) == len(same_day)


def test_t007_press_list_ignores_items_before_first_date():
    # 陰性対照: 日付見出しより前にあるリンクは日付不明のまま採らない
    html = (
        '<a class="list-press__link" href="/jp/tyoukanpress/202608/01_a.html">'
        '<span class="label label--default">午前</span>'
        '<span class="list-press__description">見出し前</span></a>'
        '<h3 class="list-press__date">令和8年8月28日</h3>'
        '<a class="list-press__link" href="/jp/tyoukanpress/202608/28_a.html">'
        '<span class="label label--default">午後</span>'
        '<span class="list-press__description">見出し後</span></a>'
    )
    items = parse_kantei_press_list(html, "https://www.kantei.go.jp/jp/tyoukanpress/index.html")
    assert [it["title"] for it in items] == ["午後 見出し後"]
    assert items[0]["date"] == "2026-08-28"


# ---- T-008: 会見(statement)と談話(discourse)を 1 枚に束ねる ---------------


def test_t008_statement_card_merges_both_sections():
    co = company("kantei_statement")
    items = fetch_company_full(co, fixture_get(co))["items"]
    paths = {it["url"] for it in items}
    assert any("/statement/" in u for u in paths), "会見側が束に入っていない"
    assert any("/discourse/" in u for u in paths), "指示・談話側が束に入っていない"
    dates = [it["date"] for it in items]
    assert dates == sorted(dates, reverse=True), "日付降順になっていない"


def test_t009_partial_section_failure_fails_whole_card():
    # 片側 0 件を「取得成功」に見せない(部分欠落の沈黙を防ぐ)
    co = company("kantei_statement")
    real = fixture_get(co)

    def broken(url, ua):
        if "/discourse/" in url:
            return "<html><body>お探しのページは見つかりません</body></html>".encode("utf-8")
        return real(url, ua)

    assert fetch_company_full(co, broken)["items"] == []
    # 陽性対照: 壊さなければ取れる(検査そのものが空振りしていないこと)
    assert fetch_company_full(co, real)["items"]


# ---- T-010: 解決済み source_url が宣言値を上書きする ----------------------


def test_t010_pipeline_overrides_source_url_on_success():
    co = {
        "id": "x",
        "name": "X",
        "source_url": "https://www.kantei.go.jp/jp/105/actions/index.html",
        "allowed_domains": ["kantei.go.jp"],
    }
    item = {"title": "t", "url": "https://www.kantei.go.jp/a.html", "date": "2026-08-28"}
    resolved = "https://www.kantei.go.jp/jp/106/actions/index.html"

    data, code = collect(
        [co], lambda c: {"items": [item], "source_url": resolved}, None, "N"
    )
    assert code == 0 and data["companies"][0]["source_url"] == resolved

    # source_url 空 → 宣言値のまま
    data, _ = collect([co], lambda c: {"items": [item], "source_url": ""}, None, "N")
    assert data["companies"][0]["source_url"] == co["source_url"]

    # 旧来の list 返却も引き続き受け付ける(既存機関の経路)
    data, _ = collect([co], lambda c: [item], None, "N")
    assert data["companies"][0]["source_url"] == co["source_url"]


def test_t010_failure_keeps_declared_source_url():
    co = {
        "id": "x",
        "name": "X",
        "source_url": "https://www.kantei.go.jp/jp/105/actions/index.html",
        "allowed_domains": ["kantei.go.jp"],
    }
    data, code = collect([co], lambda c: {"items": [], "source_url": ""}, None, "N")
    assert code == 1
    assert data["companies"][0]["ok"] is False
    assert data["companies"][0]["source_url"] == co["source_url"]
