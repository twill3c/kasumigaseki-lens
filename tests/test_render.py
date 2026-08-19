# T-201〜T-204: レンダラの内容・リンク・決定論・劣化表示
import pytest

from src.render import render_html

pytestmark = pytest.mark.integration


def sample_data(ok_all=True):
    companies = []
    for i in range(15):
        companies.append(
            {
                "id": f"co{i:02d}",
                "name": f"機関{i}",
                "source_url": f"https://co{i:02d}.example.co.jp/news/",
                "fetched_at": "2026-08-20T03:00:00Z",
                "ok": True,
                "items": [
                    {
                        "title": f"機関{i} <新製品> & 発表{j}",
                        "url": f"https://co{i:02d}.example.co.jp/press/{j}.html",
                        "date": f"2026-08-{17 + j:02d}",
                    }
                    for j in range(3)
                ],
            }
        )
    if not ok_all:
        companies[2]["ok"] = False
        companies[2]["fetched_at"] = "2026-08-19T03:00:00Z"
        companies[5]["ok"] = False
        companies[5]["items"] = []
    return {"generated_at": "2026-08-20T03:00:00Z", "companies": companies}


def test_t201_contents():
    html = render_html(sample_data())
    for i in range(15):
        assert f"機関{i}" in html
    # 出典リンク(一覧ページへのリンク)
    assert 'href="https://co00.example.co.jp/news/"' in html
    # 取得時刻は JST 表記(03:00Z → 12:00 JST)
    assert "2026-08-20 12:00" in html and "JST" in html
    # 法務フッタ: 見出し・リンクのみ・出典明記
    assert "見出しとリンクのみ" in html
    # lang 指定
    assert 'lang="ja"' in html
    # フッタは hodo-hangenki 準拠の 5 リンク構成
    assert 'href="https://github.com/twill3c/kasumigaseki-lens/blob/main/LICENSE"' in html
    assert "MIT License" in html and "© 2026 坂田哲朗" in html
    assert 'href="https://github.com/twill3c/kasumigaseki-lens"' in html
    assert 'href="https://claude.ai/code/artifact/33922a13-af7b-44a2-8a2c-82473d122438"' in html
    assert 'href="https://claude.ai/code/artifact/a4ead9df-d42b-41d8-99ec-cb5bc3bddbaf"' in html
    assert "kasumigaseki-lens の歩き方" in html and "kasumigaseki-lens 設計図" in html
    assert 'href="https://app-menu-amber.vercel.app"' in html and "App Menu" in html


def test_t202_links_and_escaping():
    html = render_html(sample_data())
    assert html.count('<a href="https://co') >= 45  # 見出し 33 + 出典 11
    assert html.count('class="headline"') == 45
    # エスケープ: 生の <新製品> がタグとして出ていない
    assert "&lt;新製品&gt; &amp; 発表0" in html
    assert "<新製品>" not in html


def test_t203_deterministic():
    a = render_html(sample_data())
    b = render_html(sample_data())
    assert a == b


def test_t204_degraded_display():
    html = render_html(sample_data(ok_all=False))
    # 前回分ありの失敗 → 劣化注記
    assert "取得失敗" in html
    # 前回分なし(items 空)でもページは壊れない
    assert "機関5" in html
