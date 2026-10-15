"""The search-text splitter keeps Bengali words whole (it once shredded them at every vowel sign)."""

import pytest

from app.core.base_service import _prefix_tsquery


@pytest.mark.parametrize(
    "typed, expected",
    [
        ("arnica", "arnica:*"),
        ("Arnica  Montana", "arnica:* & montana:*"),
        ("আর্নিকা", "আর্নিকা:*"),  # a hasanta and vowel signs inside one word
        ("মাথাব্যথা", "মাথাব্যথা:*"),
        ("জ্বর কাশি", "জ্বর:* & কাশি:*"),
        ("fever জ্বর", "fever:* & জ্বর:*"),
        ("জ্বর-কাশি", "জ্বর:* & কাশি:*"),  # punctuation still separates words
        ("র‍্যাব", "র‍্যাব:*"),  # the zero-width joiner is part of the word
        ("a&b|c!d:*", "a:* & b:* & c:* & d:*"),  # nothing that could break the tsquery gets through
    ],
)
def test_tokens_keep_words_whole(typed, expected):
    assert _prefix_tsquery(typed) == expected


@pytest.mark.parametrize("typed", ["", "   ", "&|!", "()"])
def test_no_usable_tokens_means_no_query(typed):
    assert _prefix_tsquery(typed) is None
