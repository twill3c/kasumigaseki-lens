# T-301: デプロイ設定の静的検査(vercel.json / collect.yml)
import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.validation

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_json():
    cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert cfg["outputDirectory"] == "out"
    assert cfg["buildCommand"] is None  # 静的配信のみ(ビルドなし)


def test_collect_workflow():
    text = (ROOT / ".github" / "workflows" / "collect.yml").read_text(
        encoding="utf-8"
    )
    m = re.search(r"cron:\s*['\"]([^'\"]+)['\"]", text)
    assert m, "cron 定義がない"
    hour_field = m.group(1).split()[1]
    assert hour_field.startswith("*/"), f"時フィールドが間隔指定でない: {hour_field}"
    assert int(hour_field[2:]) >= 6, "収集間隔が 6 時間未満(N-02 違反)"
    assert "workflow_dispatch" in text  # 手動 E2E 用
    assert "python -m src.fetch" in text
    assert "contents: write" in text  # bot コミットに必要
