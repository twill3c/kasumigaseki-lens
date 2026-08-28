# 霞が関レンズ(kasumigaseki-lens)

日本の中央省庁等 15 機関(首相官邸・内閣府・デジタル庁・金融庁・総務省・法務省・外務省・
財務省・文部科学省・厚生労働省・農林水産省・経済産業省・国土交通省・環境省・防衛省)の
最新報道発表を各 5 件、ヘッドライン+リンクで一望する静的サイト。
首相官邸のみ、新着情報が各系統を混ぜてしまい個々が埋もれるため、
**総理の一日 / 総理の会見・談話 / 官房長官記者会見** の 3 系統を別カードに分けており、
表示は計 18 カードになる。
[koho-lens](https://github.com/twill3c/koho-lens)(民間 IT 11 社版)の姉妹プロジェクト。

**本番**: https://kasumigaseki-lens.vercel.app

## 仕組み

```
GitHub Actions cron(6 時間間隔)
  → python -m src.fetch(18 カードを収集 → data/releases.json → out/index.html)
  → data: snapshot コミット
  → Vercel Git 連携が out/ を自動配信
```

- 取得経路は [src/sources.py](src/sources.py) に宣言的に定義(feed / html / sitemap)
- 1 機関の取得失敗は全体を止めず、前回分を保持して「取得失敗」表示(グレースフル劣化)
- 官邸の系統一覧 URL は代番号入り(`/jp/105/…`)のため決め打ちせず、トップページから解決する
- ランタイム依存は Python 標準ライブラリのみ

## 開発

```bash
python -m pytest -q        # テスト(pytest のみ dev 依存)
python -m src.fetch        # 手動収集+レンダリング
python tools/refetch_fixtures.py  # テストフィクスチャ再取得(専用コミットで)
```

仕様は [SPEC.md](SPEC.md)、テスト対応は [TEST_SPEC.md](TEST_SPEC.md) を参照。

## 法務・収集ポリシー

- 保存・表示するのは各機関が公式公開する**見出し・リンク・日付のみ**(本文は保存しない)
- 収集は 6 時間間隔。User-Agent に本リポジトリ URL を明記
- 各発表の利用条件は出典サイトの利用規約(政府標準利用規約等)に従う。出典は各機関公式サイトへリンク
