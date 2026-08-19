# T-003: 相対 URL の絶対化と、G-03 のドメイン検査ヘルパ
import pytest

from src.urlutil import absolutize, in_domains

pytestmark = pytest.mark.unit


def test_absolutize_relative():
    assert (
        absolutize("https://x.co.jp/news/index.html", "/press/1.html")
        == "https://x.co.jp/press/1.html"
    )
    assert (
        absolutize("https://x.co.jp/news/", "detail/2.html")
        == "https://x.co.jp/news/detail/2.html"
    )


def test_absolutize_absolute_passthrough():
    assert (
        absolutize("https://x.co.jp/news/", "https://y.co.jp/press/3.html")
        == "https://y.co.jp/press/3.html"
    )


def test_absolutize_protocol_relative():
    assert (
        absolutize("https://x.co.jp/news/", "//cdn.x.co.jp/p/4.html")
        == "https://cdn.x.co.jp/p/4.html"
    )


def test_in_domains():
    assert in_domains("https://pr.x.co.jp/a.html", ["x.co.jp"])
    assert in_domains("https://x.co.jp/a.html", ["x.co.jp"])
    assert not in_domains("https://evil-x.co.jp/a.html", ["x.co.jp"])
    assert not in_domains("http://x.co.jp/a.html", ["x.co.jp"])  # https 以外は不可
