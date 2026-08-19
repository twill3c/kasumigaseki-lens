"""テストフィクスチャの再取得ツール(手動実行専用)。

tests/fixtures/{id}.(xml|html) に各機関の primary 応答を保存する。
法務省(moj)は一覧ハブ → 最新年ページの二段構成のため、年ページを
tests/fixtures/pages/moj/0.html に保存し、URL → ファイルの対応を
tests/fixtures/pages/moj/map.json に書く。

実行: python tools/refetch_fixtures.py
更新は専用コミット(test: update fixtures)で行うこと(TEST_SPEC 実行規約)。
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.sources import BROWSER_UA, COMPANIES, PROJECT_UA  # noqa: E402
from src.urlutil import absolutize  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def get(url: str, ua: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": ua, "Accept-Language": "ja"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    for co in COMPANIES:
        ua = BROWSER_UA if co.get("ua") == "browser" else PROJECT_UA
        raw = get(co["primary_url"], ua)
        ext = "xml" if co["strategy"] == "feed" else "html"
        (FIX / f"{co['id']}.{ext}").write_bytes(raw)
        print(f"{co['id']}: primary {len(raw)} bytes")
        if co["id"] == "moj":
            hub = raw.decode("utf-8", "ignore")
            m = re.search(r'href="(/hisho/kouhou/press_r\d+[^"]*\.html)"', hub)
            year_url = absolutize(co["primary_url"], m.group(1))
            time.sleep(1)
            body = get(year_url, ua)
            pages = FIX / "pages" / "moj"
            pages.mkdir(parents=True, exist_ok=True)
            (pages / "0.html").write_bytes(body)
            (pages / "map.json").write_text(
                json.dumps({year_url: "0.html"}, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            print(f"  page {year_url} → 0.html ({len(body)} bytes)")
        time.sleep(1)


if __name__ == "__main__":
    main()
