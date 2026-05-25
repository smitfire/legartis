from app.segmentation import segment


def test_segments_three_sentences_in_order() -> None:
    assert segment("First sentence. Second sentence. Third sentence.") == [
        "First sentence.",
        "Second sentence.",
        "Third sentence.",
    ]


def test_treats_abbreviation_in_proper_noun_as_part_of_same_sentence() -> None:
    text = "Mr. Smith signed the agreement on Jan. 1, 2025. The deal closed."
    assert segment(text) == [
        "Mr. Smith signed the agreement on Jan. 1, 2025.",
        "The deal closed.",
    ]


def test_strips_markdown_heading_marker_but_keeps_heading_text() -> None:
    text = "# Confidentiality\nEach party shall keep the information confidential."
    sentences = segment(text)
    assert "Confidentiality" in sentences[0]
    assert not sentences[0].startswith("#")
    assert sentences[-1] == "Each party shall keep the information confidential."


def test_strips_list_bullet_markers_so_each_item_is_its_own_sentence() -> None:
    text = "- Termination requires notice.\n- Confidentiality survives termination."
    assert segment(text) == [
        "Termination requires notice.",
        "Confidentiality survives termination.",
    ]


def test_returns_empty_list_for_whitespace_only_input() -> None:
    assert segment("   \n\n\t  ") == []
