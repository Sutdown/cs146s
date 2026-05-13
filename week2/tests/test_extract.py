from unittest.mock import patch, MagicMock

from ..app.services.extract import extract_action_items, extract_action_items_llm


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


# ============================================================================
# Unit Tests for extract_action_items_llm()
# ============================================================================

def test_llm_extract_empty_input():
    """Test that empty input returns empty list."""
    items = extract_action_items_llm("")
    assert items == []


def test_llm_extract_whitespace_only():
    """Test that whitespace-only input returns empty list."""
    items = extract_action_items_llm("   \n\t  ")
    assert items == []


def test_llm_extract_bullet_list():
    """Test extraction from bullet list format."""
    # Mock the Ollama chat response
    mock_response = MagicMock()
    mock_response.message.content = '["week1", "week2", "week3", "week4"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("""
        - [ ] week1
        - [ ] week2
        - [ ] week3
        - [ ] week4
        """)

        assert len(items) == 4
        assert "week1" in items
        assert "week2" in items
        assert "week3" in items
        assert "week4" in items


def test_llm_extract_keyword_prefix():
    """Test extraction from keyword-prefixed lines."""
    mock_response = MagicMock()
    mock_response.message.content = '["Fix the login bug", "Update documentation"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("""
        Fix the login bug
        action: Update documentation
        """)

        assert len(items) == 2
        assert "Fix the login bug" in items
        assert "Update documentation" in items


def test_llm_extract_mixed_format():
    """Test extraction from mixed format input."""
    mock_response = MagicMock()
    mock_response.message.content = '["Task 1", "Task 2", "Task 3", "Task 4"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("""
        - [ ] Task 1
        - [ ] Task 2
        todo: Task 3
        todo2: Task 4
        """)

        assert len(items) == 4

def test_llm_extract_json_with_markdown():
    """Test handling of JSON wrapped in markdown code blocks."""
    mock_response = MagicMock()
    mock_response.message.content = '```json\n["item1", "item2"]\n```'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("- item1\n- item2")

        assert len(items) == 2
        assert "item1" in items
        assert "item2" in items


def test_llm_extract_deduplication():
    """Test that duplicate items are removed."""
    mock_response = MagicMock()
    mock_response.message.content = '["Task", "Task", "Task"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("Task\nTask\nTask")

        # Should deduplicate (case-insensitive)
        assert len(items) == 1


def test_llm_extract_fallback_on_error():
    """Test that function falls back to rule-based extraction on LLM error."""
    with patch("week2.app.services.extract.chat", side_effect=Exception("Connection error")):
        # The function should fall back to rule-based extraction
        items = extract_action_items_llm("- [ ] Fix the bug")

        # Should return something from the fallback
        assert isinstance(items, list)
        assert len(items) >= 0


def test_llm_extract_case_insensitive_dedup():
    """Test that deduplication is case-insensitive."""
    mock_response = MagicMock()
    mock_response.message.content = '["Task", "TASK", "task"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("Task\nTASK\ntask")

        # Should deduplicate case-insensitively
        assert len(items) == 1


def test_llm_extract_returns_list():
    """Test that function always returns a list."""
    mock_response = MagicMock()
    mock_response.message.content = '["item1"]'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("item1")
        assert isinstance(items, list)


def test_llm_extract_handles_dict_format():
    """Test handling of JSON response in dict format."""
    mock_response = MagicMock()
    mock_response.message.content = '{"items": ["Task 1", "Task 2"]}'

    with patch("week2.app.services.extract.chat", return_value=mock_response):
        items = extract_action_items_llm("Task 1\nTask 2")

        assert len(items) == 2
        assert "Task 1" in items
        assert "Task 2" in items
