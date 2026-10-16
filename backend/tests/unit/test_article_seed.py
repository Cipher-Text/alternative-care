"""The starter articles file is well formed: it passes the same rules the authoring API enforces."""
import json

from app.shared.models.article import ARTICLE_DISCIPLINES, EVIDENCE_LABELS
from app.shared.schemas.article import parse_youtube_id
from scripts.catalogue.build import SEED


def _items() -> list[dict]:
    return json.loads((SEED / "articles.json").read_text(encoding="utf-8"))["articles"]


def test_ten_articles_and_five_videos_with_unique_slugs():
    items = _items()
    assert sum(i["kind"] == "article" for i in items) == 10
    assert sum(i["kind"] == "video" for i in items) == 5
    assert len({i["slug"] for i in items}) == len(items)


def test_every_item_is_complete_and_in_bangla():
    for i in _items():
        assert i["discipline"] in ARTICLE_DISCIPLINES and i["evidence_label"] in EVIDENCE_LABELS
        assert i["title_bn"] and i["summary_bn"] and i["body_bn"] and i["title_en"] and i["summary_en"]
        assert any("ঀ" <= c <= "৿" for c in i["body_bn"])
        assert len(i["summary_bn"]) <= 1000 and len(i["title_bn"]) <= 300
        if i["kind"] == "video":
            assert parse_youtube_id(i["youtube_id"]) == i["youtube_id"]
        else:
            assert i["youtube_id"] is None and len(i["body_bn"]) > 600
