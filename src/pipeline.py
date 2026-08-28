"""収集パイプライン(T-101〜T-105)。

collect(companies, fetcher, prev, now) -> (data, exit_code)

- fetcher(company) -> list[items] または {"items": [...], "source_url": str}。
  例外 or 0 件は「失敗」: ok=False とし、prev に同 id があればその items /
  fetched_at を引き継ぐ(グレースフル劣化 F-05)
- 取得成功時に source_url が返れば宣言値を上書きする(官邸の代番号のように
  一覧ページ URL 自体が動く機関のため)
- 成功時は items を最新 5 件に切り詰め fetched_at=now
- exit_code: 全社失敗のみ 1(G-04)
"""

from __future__ import annotations

MAX_ITEMS = 5


def _prev_company(prev: dict | None, cid: str) -> dict | None:
    if not prev:
        return None
    return next((c for c in prev.get("companies", []) if c["id"] == cid), None)


def collect(companies, fetcher, prev, now):
    out = []
    ok_count = 0
    for co in companies:
        record = {
            "id": co["id"],
            "name": co["name"],
            "source_url": co["source_url"],
            "fetched_at": now,
            "ok": False,
            "items": [],
        }
        resolved_url = ""
        try:
            result = fetcher(co)
            if isinstance(result, dict):  # fetch_company_full 形式
                items = result.get("items") or []
                resolved_url = result.get("source_url") or ""
            else:
                items = result
        except Exception:
            items = []
        if items:
            record["ok"] = True
            record["items"] = list(items)[:MAX_ITEMS]
            if resolved_url:
                record["source_url"] = resolved_url
            ok_count += 1
        else:
            old = _prev_company(prev, co["id"])
            if old:
                record["items"] = old["items"]
                record["fetched_at"] = old["fetched_at"]
        out.append(record)
    data = {"generated_at": now, "companies": out}
    return data, (0 if ok_count > 0 else 1)
