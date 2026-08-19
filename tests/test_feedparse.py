# T-004: RSS1.0(RDF) / RSS2.0 / Atom の最小合成フィードを共通パーサが読める
import pytest

from src.feedparse import parse_feed

pytestmark = pytest.mark.unit

RSS10 = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel rdf:about="https://example.co.jp/rss"><title>News</title></channel>
  <item rdf:about="https://example.co.jp/press/1.html">
    <title>リリース一</title>
    <link>https://example.co.jp/press/1.html</link>
    <dc:date>2026-08-19T10:00:00+09:00</dc:date>
  </item>
  <item rdf:about="https://example.co.jp/press/2.html">
    <title>リリース二</title>
    <link>https://example.co.jp/press/2.html</link>
    <dc:date>2026-08-18T10:00:00+09:00</dc:date>
  </item>
  <item rdf:about="https://example.co.jp/press/3.html">
    <title>リリース三</title>
    <link>https://example.co.jp/press/3.html</link>
    <dc:date>2026-08-17T10:00:00+09:00</dc:date>
  </item>
</rdf:RDF>
"""

RSS20 = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>News</title>
  <item><title>リリース一</title><link>https://example.co.jp/press/1.html</link>
    <pubDate>Wed, 19 Aug 2026 10:00:00 +0900</pubDate></item>
  <item><title>リリース二</title><link>https://example.co.jp/press/2.html</link>
    <pubDate>Tue, 18 Aug 2026 10:00:00 +0900</pubDate></item>
  <item><title>リリース三</title><link>https://example.co.jp/press/3.html</link>
    <pubDate>Mon, 17 Aug 2026 10:00:00 +0900</pubDate></item>
</channel></rss>
"""

ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>News</title>
  <entry><title>リリース一</title>
    <link rel="alternate" href="https://example.co.jp/press/1.html"/>
    <updated>2026-08-19T10:00:00+09:00</updated></entry>
  <entry><title>リリース二</title>
    <link href="https://example.co.jp/press/2.html"/>
    <updated>2026-08-18T10:00:00+09:00</updated></entry>
  <entry><title>リリース三</title>
    <link href="https://example.co.jp/press/3.html"/>
    <updated>2026-08-17T10:00:00+09:00</updated></entry>
</feed>
"""


@pytest.mark.parametrize("raw", [RSS10, RSS20, ATOM], ids=["rss10", "rss20", "atom"])
def test_parse_three_formats(raw):
    items = parse_feed(raw.encode("utf-8"))
    assert len(items) == 3
    assert items[0]["title"] == "リリース一"
    assert items[0]["url"] == "https://example.co.jp/press/1.html"
    assert items[0]["date"] == "2026-08-19"
    assert [i["date"] for i in items] == ["2026-08-19", "2026-08-18", "2026-08-17"]


def test_parse_feed_garbage_raises():
    with pytest.raises(ValueError):
        parse_feed(b"<html><body>not a feed</body></html>")
