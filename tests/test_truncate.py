from newsroom.filtering import truncate_text

def test_truncate_text_shorter_than_limit():
    assert truncate_text("hello", 10) == "hello"

def test_truncate_text_exact_limit():
    assert truncate_text("hello", 5) == "hello"

def test_truncate_text_longer_than_limit():
    assert truncate_text("hello world", 8) == "hello..."

def test_truncate_text_strips_whitespace():
    assert truncate_text("  hello  ", 10) == "hello"

def test_truncate_text_handles_none():
    assert truncate_text(None, 10) == ""

def test_truncate_text_small_limit():
    assert truncate_text("abcde", 3) == "..."

def test_truncate_text_limit_four():
    assert truncate_text("long text", 4) == "l..."

def test_truncate_text_rstrip_before_ellipsis():
    # "hello " is 6 chars, limit is 9. 9-3=6.
    # But wait, "hello world", limit 9 -> 9-3=6. text[:6] is "hello ".
    # rstrip() should remove that space.
    assert truncate_text("hello world", 9) == "hello..."

def test_truncate_text_empty_string():
    assert truncate_text("", 5) == ""

def test_truncate_text_very_small_limit():
    # If limit is smaller than ellipsis length, it should probably still respect the limit
    # or at least not return a string longer than the input.
    # Current implementation returns "abc..." for limit=2, text="abcde"
    # because text[:2-3] is text[:-1]
    assert len(truncate_text("abcde", 2)) <= 2
