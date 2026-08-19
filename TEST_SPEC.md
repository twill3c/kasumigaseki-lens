# TEST_SPEC.md — kasumigaseki-lens

<!-- scaffold template v1.8.0 から展開(2026-08-20) -->

## 実行規約

- `python -m pytest -q` を stage 3–5 の判定に使用。マーカー: `unit` / `integration` / `validation`
- フィクスチャ更新は専用コミット(`test: update fixtures`)で行い、理由をループログに記す
- フィクスチャは実サイトから保存した生 HTML/フィード(`tests/fixtures/{company_id}.*`)。
  バイナリ同一性維持のため `.gitattributes` で `-text` 指定(CRLF 汚染防止 — hodo-hangenki の教訓)
- 解析解を期待する合成フィクスチャは、期待値の導出前提をテスト内の assert で検算する(HC-004 予防)

## ケース一覧

| ID | 対応要求 | ケース | 期待 |
|---|---|---|---|
| T-001 | F-01/G-01 | 各機関フィクスチャ → パーサ(15 機関パラメトライズ) | 3 件以上抽出。タイトル非空・URL 絶対 https・日付 ISO(YYYY-MM-DD) |
| T-002 | G-03 | 抽出 URL のドメイン検査 | 全 URL が当該会社の許可ドメインに属する |
| T-003 | F-01 | 相対 URL を含むフィクスチャ | ベース URL で絶対化される |
| T-004 | F-01 | RSS1.0(RDF)/ RSS2.0 / Atom の最小合成フィード | 共通フィードパーサが 3 形式とも title/link/date を抽出 |
| T-005 | F-01 | 日付形式方言(RFC822 / ISO8601±TZ / 和文 YYYY年M月D日 / YYYY.M.D / NA) | すべて YYYY-MM-DD に正規化。パース不能は空文字(例外にしない) |
| T-101 | F-02/G-02 | fetch 結果のマージ → releases.json | スキーマ準拠・companies は定義順 11 要素・items ≤3 |
| T-102 | F-05/G-04 | 1 機関の fetch が例外 → 前回データあり | 当該社 ok=false・前回 items 引き継ぎ・他社は更新・exit 0 |
| T-103 | F-05/G-04 | 1 機関の fetch が例外 → 前回データなし | 当該社 ok=false・items=[]・exit 0 |
| T-104 | G-04 | 全 15 機関失敗 | exit 1(サイレント全滅を防ぐ) |
| T-105 | N-03 | 1 機関のパーサが 0 件抽出 | 例外でなく ok=false 扱い(0 件は失敗とみなす) |
| T-201 | F-03/N-02 | render 出力の内容検査 | 15 機関の機関名・出典リンク・取得時刻(JST 表記)・法務フッタが含まれる |
| T-202 | F-03/G-05 | render のリンク検査 | `<a href="https://...">` 総数 = Σ items。タイトルは HTML エスケープ済み |
| T-203 | N-04 | 同一 JSON で 2 回 render | バイト同一 |
| T-204 | F-03 | ok=false の会社を含む JSON | 「取得失敗(前回分を表示)」等の劣化表示が出る |
| T-301 | F-04 | vercel.json / collect.yml の静的検査 | outputDirectory=out・buildCommand null・cron 間隔 ≥6h |
