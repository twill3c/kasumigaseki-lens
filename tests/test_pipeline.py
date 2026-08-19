# T-101〜T-105: マージ・グレースフル劣化・exit code
import pytest

from src.pipeline import collect

pytestmark = pytest.mark.integration

NOW = "2026-08-20T03:00:00Z"


def fake_companies(n=11):
    return [
        {
            "id": f"co{i:02d}",
            "name": f"会社{i}",
            "source_url": f"https://co{i:02d}.example.co.jp/news/",
            "allowed_domains": [f"co{i:02d}.example.co.jp"],
        }
        for i in range(n)
    ]


def items_for(cid, n=4):
    return [
        {
            "title": f"{cid} リリース{j}",
            "url": f"https://{cid}.example.co.jp/press/{j}.html",
            "date": f"2026-08-{10 + j:02d}",
        }
        for j in range(n, 0, -1)
    ]


def ok_fetcher(company):
    return items_for(company["id"])


def test_t101_schema_and_order():
    companies = fake_companies()
    data, code = collect(companies, ok_fetcher, prev=None, now=NOW)
    assert code == 0
    assert data["generated_at"] == NOW
    assert [c["id"] for c in data["companies"]] == [c["id"] for c in companies]
    assert len(data["companies"]) == 11
    for c in data["companies"]:
        assert c["ok"] is True
        assert c["fetched_at"] == NOW
        assert len(c["items"]) == 3  # 4 件返っても 3 件に切る
        for it in c["items"]:
            assert it["title"] and it["url"].startswith("https://") and it["date"]


def _failing_for(bad_ids, exc=RuntimeError("boom")):
    def fetcher(company):
        if company["id"] in bad_ids:
            raise exc
        return items_for(company["id"])

    return fetcher


def test_t102_partial_failure_keeps_prev():
    companies = fake_companies()
    prev, _ = collect(companies, ok_fetcher, prev=None, now="2026-08-19T21:00:00Z")
    data, code = collect(companies, _failing_for({"co03"}), prev=prev, now=NOW)
    assert code == 0
    bad = next(c for c in data["companies"] if c["id"] == "co03")
    assert bad["ok"] is False
    assert bad["items"] == prev["companies"][3]["items"]  # 前回分を保持
    assert bad["fetched_at"] == "2026-08-19T21:00:00Z"  # 取得時刻も前回のまま
    good = next(c for c in data["companies"] if c["id"] == "co04")
    assert good["ok"] is True and good["fetched_at"] == NOW


def test_t103_failure_without_prev():
    companies = fake_companies()
    data, code = collect(companies, _failing_for({"co03"}), prev=None, now=NOW)
    assert code == 0
    bad = next(c for c in data["companies"] if c["id"] == "co03")
    assert bad["ok"] is False and bad["items"] == []


def test_t104_all_fail_exit_1():
    companies = fake_companies()
    data, code = collect(
        companies, _failing_for({c["id"] for c in companies}), prev=None, now=NOW
    )
    assert code == 1
    assert all(c["ok"] is False for c in data["companies"])


def test_t105_zero_items_is_failure():
    companies = fake_companies()

    def fetcher(company):
        if company["id"] == "co05":
            return []
        return items_for(company["id"])

    prev, _ = collect(companies, ok_fetcher, prev=None, now="2026-08-19T21:00:00Z")
    data, code = collect(companies, fetcher, prev=prev, now=NOW)
    assert code == 0
    bad = next(c for c in data["companies"] if c["id"] == "co05")
    assert bad["ok"] is False
    assert bad["items"] == prev["companies"][5]["items"]
