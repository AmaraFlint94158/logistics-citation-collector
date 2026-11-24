from src.citation_collector import dedupe_citations


def test_duplicate_source_urls_keep_the_first_record():
    records = [
        {"title": "Carrier scan", "url": "https://example.test/scan", "source": "carrier"},
        {"title": "Same scan", "url": "https://example.test/scan", "source": "mirror"},
        {"title": "POD guide", "url": "https://example.test/pod", "source": "archive"},
    ]

    result = dedupe_citations(records)

    assert result[0].title == "Carrier scan"
    assert [citation.url for citation in result] == [
        "https://example.test/scan", "https://example.test/pod"
    ]
