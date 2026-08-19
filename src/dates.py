"""日付文字列の正規化(T-005)。

対応方言: RFC822(pubDate)/ ISO8601(±TZ, Z)/ 和文 YYYY年M月D日 /
YYYY.M.D / YYYY/M/D / YYYY-MM-DD。パース不能は空文字を返し、例外にしない。
返す日付はソース表記の暦日(タイムゾーン変換はしない — 発表日として扱う)。
"""

from __future__ import annotations

import re
from email.utils import parsedate_to_datetime

_NUMERIC = re.compile(r"(\d{4})[./\-年](\d{1,2})[./\-月](\d{1,2})")
_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})T")
# 元号: 令和 N → 2018+N。平成 N は本来 1989 改元だが、省庁サイトに平成を
# 継続換算した表記(平成38年=2026年)が実在するため 1988+N で扱う
_ERA = re.compile(r"(令和|平成)(\d+)年(\d{1,2})月(\d{1,2})日")
_ERA_BASE = {"令和": 2018, "平成": 1988}
_FULLWIDTH = str.maketrans("0123456789", "0123456789")


def normalize_date(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    s = raw.strip().translate(_FULLWIDTH)
    if not s:
        return ""
    s = s.replace(" JST", " +0900")  # 金融庁 RSS の非標準 TZ トークン
    m = _ERA.search(s)
    if m:
        era, n, mo, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return f"{_ERA_BASE[era] + n:04d}-{mo:02d}-{d:02d}"
    m = _ISO.match(s) or _NUMERIC.search(s)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        return ""
    try:
        dt = parsedate_to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""
