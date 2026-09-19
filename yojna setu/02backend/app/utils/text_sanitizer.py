"""
Text Normalization & Display Sanitizer Utility for YojnaSetu.

Provides robust, multi-pass cleaning of government scheme titles, descriptions,
ministries, and metadata without modifying canonical database storage.

Key features:
- Multi-pass HTML entity decoding (&quot; -> ", &amp; -> &, &amp;amp; -> &, &lt; -> <, etc.)
- Raw HTML tag conversion (<br>, <p>, etc.) to clean whitespace/newlines
- Markdown artifact removal (**bold** -> bold, stray **, __, etc.)
- Whitespace and duplicate punctuation normalization
- Overview vs. full details splitting for clean progressive disclosure
"""

import html
import re
from typing import Optional, Tuple


def normalize_gov_text(text: Optional[str]) -> str:
    """
    Cleans raw, scraped, or double-encoded text into clean, readable civic copy.
    Preserves government content and semantic meaning while removing web artifacts.
    """
    if not text:
        return ""

    cur = str(text)

    # 1. Convert <br> and paragraph variants to space or newline
    cur = re.sub(r"(?i)<br\s*/?>", " ", cur)
    cur = re.sub(r"(?i)</?p\s*>", "\n", cur)
    cur = re.sub(r"(?i)</?div\s*>", "\n", cur)
    # Strip any remaining actual HTML tags safely (requires tag name to start with letter or !)
    cur = re.sub(r"<(?:\/?[a-zA-Z][a-zA-Z0-9]*|!--)[^>]*>", " ", cur)

    # 2. Multi-pass HTML entity unescaping (handles &amp;quot;, &amp;amp;, etc.)
    prev = ""
    for _ in range(3):
        cur = html.unescape(cur)
        if cur == prev:
            break
        prev = cur

    # 3. Normalize special unicode quotes, apostrophes, and replacement characters
    cur = cur.replace("\ufffd", "'")
    cur = cur.replace("\u2018", "'").replace("\u2019", "'")
    cur = cur.replace("\u201c", '"').replace("\u201d", '"')
    cur = cur.replace("\u2013", "-").replace("\u2014", "-")
    cur = cur.replace("\xa0", " ")

    # 4. Remove Markdown formatting artifacts (**bold**, __italic__, headers)
    cur = re.sub(r"\*\*([^*]+)\*\*", r"\1", cur)
    cur = re.sub(r"__([^_]+)__", r"\1", cur)
    cur = cur.replace("**", "").replace("__", "")
    cur = re.sub(r"^\s*#+\s*", "", cur, flags=re.MULTILINE)

    # 5. Clean repeated whitespace and blank lines
    cur = re.sub(r"[ \t]+", " ", cur)
    cur = re.sub(r"\n\s*\n+", "\n\n", cur)

    return cur.strip()


def clean_gov_title(title: Optional[str]) -> str:
    """
    Cleans a scheme or partner title.
    Strips redundant wrapping quotes if present, while preserving valid internal quotes.
    """
    cleaned = normalize_gov_text(title)
    if not cleaned:
        return ""

    # If the entire title is wrapped in matched quotes like "Something", unwrap
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        if len(cleaned) > 2:
            cleaned = cleaned[1:-1].strip()

    # Clean double quotes that were escaped awkwardly: e.g. ""Title""
    cleaned = re.sub(r'^"+|"+$', '', cleaned).strip()

    return cleaned


def clean_gov_description(desc: Optional[str], max_words: Optional[int] = None) -> str:
    """
    Cleans and optionally truncates a description at word boundaries with an ellipsis.
    """
    cleaned = normalize_gov_text(desc)
    if not cleaned:
        return ""

    if max_words and max_words > 0:
        words = cleaned.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."

    return cleaned


def split_overview_and_details(text: Optional[str], target_words: int = 40) -> Tuple[str, str]:
    """
    Splits a long government description into a concise overview paragraph
    and the remaining full details text for progressive disclosure.
    """
    cleaned = normalize_gov_text(text)
    if not cleaned:
        return "", ""

    # If it's already short, entire text is the overview and full details
    words = cleaned.split()
    if len(words) <= target_words:
        return cleaned, cleaned

    # Look for a sentence boundary near target_words
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    overview_sentences = []
    word_count = 0

    for s in sentences:
        s_words = len(s.split())
        if word_count + s_words <= target_words + 15 or not overview_sentences:
            overview_sentences.append(s)
            word_count += s_words
        else:
            break

    overview = " ".join(overview_sentences).strip()
    return overview, cleaned
