# T-001/T-002: 実サイトの保存フィクスチャに対して 11 社全パーサを検証(G-01/G-03)
import json
import re
from pathlib import Path

import pytest

from src.fetchers import fetch_company
from src.sources import COMPANIES
from src.urlutil import in_domains

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent / "fixtures"


def fixture_get(company):
    """primary_url とサイトマップ記事 URL をフィクスチャファイルに解決する get()。"""
    ext = "xml" if company["strategy"] == "feed" else "html"
    mapping = {company["primary_url"]: FIX / f"{company['id']}.{ext}"}
    map_json = FIX / "pages" / company["id"] / "map.json"
    if map_json.exists():
        for url, fname in json.loads(map_json.read_text(encoding="utf-8")).items():
            mapping[url] = FIX / "pages" / company["id"] / fname

    def get(url, ua):
        assert isinstance(ua, str) and ua
        if url not in mapping:
            raise AssertionError(f"フィクスチャに無い URL への fetch: {url}")
        return mapping[url].read_bytes()

    return get


@pytest.mark.parametrize("company", COMPANIES, ids=[c["id"] for c in COMPANIES])
def test_t001_extracts_three_items(company):
    items = fetch_company(company, fixture_get(company))
    assert len(items) >= 3, f"{company['id']}: {len(items)} 件しか抽出できない"
    for it in items[:3]:
        assert it["title"].strip(), f"{company['id']}: 空タイトル"
        assert "<" not in it["title"], f"{company['id']}: タイトルにタグ残骸"
        assert it["url"].startswith("https://"), f"{company['id']}: {it['url']}"
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", it["date"]), (
            f"{company['id']}: 日付不正 {it['date']!r}"
        )


@pytest.mark.parametrize("company", COMPANIES, ids=[c["id"] for c in COMPANIES])
def test_t002_urls_in_allowed_domains(company):
    items = fetch_company(company, fixture_get(company))
    for it in items[:3]:
        assert in_domains(it["url"], company["allowed_domains"]), (
            f"{company['id']}: 許可外ドメイン {it['url']}"
        )
