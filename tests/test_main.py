"""
Unit tests for pure functions in main.py.
These tests do NOT call any external API — they only test parsing and formatting logic.
"""

import sys
from pathlib import Path

# Add project root to path so we can import main.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the pure functions we want to test
from main import parse_output, word_count, slugify


# ---------- parse_output tests ----------

def test_parse_output_inline_script():
    """SCRIPT on same line as label."""
    raw = """TITLE: Why Ice Is Slippery
HOOK: You might think ice is
SCRIPT: You might think ice is slippery because it's cold. Actually, a thin layer of water forms on top, making it slick. That's why we slip!"""
    result = parse_output(raw)
    assert result["title"] == "Why Ice Is Slippery"
    assert result["hook"] == "You might think ice is"
    assert "thin layer of water" in result["script"]
    assert word_count(result["script"]) >= 20


def test_parse_output_multiline_script():
    """SCRIPT label on its own line, content follows on next lines."""
    raw = """TITLE: How Magnets Work
HOOK: Magnets seem like magic
SCRIPT:
Magnets seem like magic, but the secret is inside. Tiny electrons spin and align. Their forces combine into one field. This pushes and pulls metals. Did you know Earth is a magnet?"""
    result = parse_output(raw)
    assert result["title"] == "How Magnets Work"
    assert result["hook"] == "Magnets seem like magic"
    assert "electrons spin" in result["script"]
    assert word_count(result["script"]) >= 25


def test_parse_output_missing_title():
    """No TITLE line — should still extract HOOK and SCRIPT."""
    raw = """HOOK: Test hook here
SCRIPT: This is a test script with enough words to be considered a valid script for the parser."""
    result = parse_output(raw)
    assert result["title"] == ""
    assert result["hook"] == "Test hook here"
    assert "test script" in result["script"]


def test_parse_output_empty():
    """Completely empty input should return empty fields."""
    result = parse_output("")
    assert result["title"] == ""
    assert result["hook"] == ""
    assert result["script"] == ""


# ---------- word_count tests ----------

def test_word_count_simple():
    assert word_count("one two three") == 3


def test_word_count_with_punctuation():
    assert word_count("Hello, world! How are you?") == 5


def test_word_count_with_hyphens():
    assert word_count("state-of-the-art technology") == 2


def test_word_count_empty():
    assert word_count("") == 0


def test_word_count_contractions():
    assert word_count("don't can't won't") == 3


# ---------- slugify tests ----------

def test_slugify_basic():
    assert slugify("Why Ice Is Slippery") == "why-ice-is-slippery"


def test_slugify_with_punctuation():
    assert slugify("How Magnets Work!") == "how-magnets-work"


def test_slugify_with_numbers():
    assert slugify("Top 10 Facts") == "top-10-facts"


def test_slugify_long_text_truncated():
    """Slug should be truncated to 40 characters."""
    long_text = "this is a very long topic title that should be truncated by the slugify function"
    result = slugify(long_text)
    assert len(result) <= 40


def test_slugify_empty_returns_untitled():
    assert slugify("") == "untitled"


def test_slugify_only_special_chars():
    assert slugify("!!!???") == "untitled"