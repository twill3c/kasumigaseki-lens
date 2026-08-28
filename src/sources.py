"""18 カード(15 機関 + 首相官邸の 3 系統)の取得経路の宣言的定義(F-06)。

strategy:
- feed: primary_url が RSS1.0/2.0/Atom フィード
- html: primary_url の静的 HTML を機関別パーサで抽出(moj は一覧ハブ → 最新年
  ページの二段取得を fetchers 側で行う)

ua:
- project(既定): PROJECT_UA
- browser: WAF が非ブラウザ UA を遮断するサイト(外務省・経産省)のみ。
  robots.txt に Disallow 全面指定が無いことを確認済み(2026-08-20、
  経産省 robots.txt は空 = 全面許可)

調査経緯(2026-08-20):
- フィード 10 機関 / HTML 5 機関(農水・環境・法務・外務・経産)
- 金融庁 RSS の pubDate は非標準トークン「JST」(dates.py で +0900 へ前処理)
- 法務省の年別一覧は日付が <!-- dt --> コメント内・元号継続換算(平成38年=2026年)
- 内閣府フィードのリンクは外局(esri.cao.go.jp / fsc.go.jp 等)に跨る
- デジタル庁・財務省・防衛省のフィードは「新着情報」(報道発表以外を含む)。
  防衛省のみ /j/press/ 配下にフィルタ

追加調査(2026-08-29 — 首相官邸の系統別カード F-07):
- 官邸の新着 RDF は総理の一日・会見・談話・官房長官会見を混ぜて流すため、
  各系統が 5 件枠から押し出される。系統別に 3 枚を追加(計 18 カード)
- 系統一覧の URL は代番号入り(/jp/105/actions/…)。総理交代で変わるので
  トップページ(https://www.kantei.go.jp/index.html)から解決する二段取得にした
- 官房長官会見(/jp/tyoukanpress/)だけは代番号を含まない固定パス
"""

PROJECT_UA = "kasumigaseki-lens/1.0 (+https://github.com/twill3c/kasumigaseki-lens)"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

COMPANIES = [
    {
        "id": "kantei",
        "name": "首相官邸 新着情報",
        "source_url": "https://www.kantei.go.jp/jp/news/index.html",
        "primary_url": "https://www.kantei.go.jp/index-jnews.rdf",
        "strategy": "feed",
        "allowed_domains": ["kantei.go.jp"],
    },
    {
        # 官邸のセクション URL は代番号を含む(/jp/105/…)ため総理交代で変わる。
        # トップページ(hub)から現行代番号を解決する二段取得にする(moj と同型)。
        "id": "kantei_actions",
        "name": "首相官邸 総理の一日",
        "source_url": "https://www.kantei.go.jp/jp/105/actions/index.html",
        "primary_url": "https://www.kantei.go.jp/index.html",
        "strategy": "html",
        "kantei_sections": ["actions"],
        "allowed_domains": ["kantei.go.jp"],
    },
    {
        # 会見(statement)と指示・談話(discourse)は別ページだが 1 枚に束ねる。
        # どちらか一方が 0 件になったら束ね全体を失敗扱いにする(部分欠落の
        # 沈黙を避ける — 経産省フィード凍結の教訓)。
        "id": "kantei_statement",
        "name": "首相官邸 総理の会見・談話",
        "source_url": "https://www.kantei.go.jp/jp/105/statement/index.html",
        "primary_url": "https://www.kantei.go.jp/index.html",
        "strategy": "html",
        "kantei_sections": ["statement", "discourse"],
        "allowed_domains": ["kantei.go.jp"],
    },
    {
        # 官房長官会見は代番号を含まない固定パス → hub 解決は不要
        "id": "kantei_tyoukanpress",
        "name": "首相官邸 官房長官記者会見",
        "source_url": "https://www.kantei.go.jp/jp/tyoukanpress/index.html",
        "primary_url": "https://www.kantei.go.jp/jp/tyoukanpress/index.html",
        "strategy": "html",
        "allowed_domains": ["kantei.go.jp"],
    },
    {
        "id": "cao",
        "name": "内閣府",
        "source_url": "https://www.cao.go.jp/press/houdou.html",
        "primary_url": "https://www.cao.go.jp/rss/news.rdf",
        "strategy": "feed",
        "allowed_domains": ["go.jp"],
    },
    {
        "id": "digital",
        "name": "デジタル庁",
        "source_url": "https://www.digital.go.jp/news",
        "primary_url": "https://www.digital.go.jp/rss/news.xml",
        "strategy": "feed",
        "allowed_domains": ["digital.go.jp"],
    },
    {
        "id": "fsa",
        "name": "金融庁",
        "source_url": "https://www.fsa.go.jp/news/index.html",
        "primary_url": "https://www.fsa.go.jp/fsaNewsListAll_rss2.xml",
        "strategy": "feed",
        "allowed_domains": ["fsa.go.jp"],
    },
    {
        "id": "soumu",
        "name": "総務省",
        "source_url": "https://www.soumu.go.jp/menu_news/s-news/index.html",
        "primary_url": "https://www.soumu.go.jp/news.rdf",
        "strategy": "feed",
        "allowed_domains": ["soumu.go.jp"],
    },
    {
        "id": "moj",
        "name": "法務省",
        "source_url": "https://www.moj.go.jp/press_index.html",
        "primary_url": "https://www.moj.go.jp/press_index.html",
        "strategy": "html",
        "allowed_domains": ["moj.go.jp"],
    },
    {
        "id": "mofa",
        "name": "外務省",
        "source_url": "https://www.mofa.go.jp/mofaj/press/release/index.html",
        "primary_url": "https://www.mofa.go.jp/mofaj/press/release/index.html",
        "strategy": "html",
        "ua": "browser",
        "allowed_domains": ["mofa.go.jp"],
    },
    {
        "id": "mof",
        "name": "財務省",
        "source_url": "https://www.mof.go.jp/news/index.html",
        "primary_url": "https://www.mof.go.jp/news.rss",
        "strategy": "feed",
        "allowed_domains": ["mof.go.jp"],
    },
    {
        "id": "mext",
        "name": "文部科学省",
        "source_url": "https://www.mext.go.jp/b_menu/news/index.html",
        "primary_url": "https://www.mext.go.jp/b_menu/news/index.rdf",
        "strategy": "feed",
        "allowed_domains": ["mext.go.jp"],
    },
    {
        "id": "mhlw",
        "name": "厚生労働省",
        "source_url": "https://www.mhlw.go.jp/stf/houdou/index.html",
        "primary_url": "https://www.mhlw.go.jp/stf/news.rdf",
        "strategy": "feed",
        "allowed_domains": ["mhlw.go.jp"],
    },
    {
        "id": "maff",
        "name": "農林水産省",
        "source_url": "https://www.maff.go.jp/j/press/index.html",
        "primary_url": "https://www.maff.go.jp/j/press/index.html",
        "strategy": "html",
        "allowed_domains": ["maff.go.jp"],
    },
    {
        # 公式 Atom(ml_index_release_atom.xml)は 2026-06-19 で更新停止
        # (サイト刷新でフィード凍結)→ press/index.html の直接抽出へ切替。
        # AWS WAF: 非ブラウザ UA は 403、ブラウザ UA も断続的に JS チャレンジ
        # (202/空ボディ)→ 0 件で ok=False となり前回分保持で凌ぐ(F-05)。
        "id": "meti",
        "name": "経済産業省",
        "source_url": "https://www.meti.go.jp/press/index.html",
        "primary_url": "https://www.meti.go.jp/press/index.html",
        "strategy": "html",
        "ua": "browser",
        "allowed_domains": ["meti.go.jp"],
    },
    {
        "id": "mlit",
        "name": "国土交通省",
        "source_url": "https://www.mlit.go.jp/report/press/index.html",
        "primary_url": "https://www.mlit.go.jp/pressrelease.rdf",
        "strategy": "feed",
        "allowed_domains": ["mlit.go.jp"],
    },
    {
        "id": "env",
        "name": "環境省",
        "source_url": "https://www.env.go.jp/press/index.html",
        "primary_url": "https://www.env.go.jp/press/index.html",
        "strategy": "html",
        "allowed_domains": ["env.go.jp"],
    },
    {
        "id": "mod",
        "name": "防衛省",
        "source_url": "https://www.mod.go.jp/j/press/news/index.html",
        "primary_url": "https://www.mod.go.jp/j/rss/news.xml",
        "strategy": "feed",
        "path_filter": "/j/press/",
        "allowed_domains": ["mod.go.jp"],
    },
]
