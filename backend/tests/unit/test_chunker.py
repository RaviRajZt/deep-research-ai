from __future__ import annotations

import pytest
from app.utils.chunker import SemanticChunker
from app.utils.token import TokenEstimator


@pytest.fixture
def estimator() -> TokenEstimator:
    return TokenEstimator()


@pytest.fixture
def chunker(estimator: TokenEstimator) -> SemanticChunker:
    return SemanticChunker(token_estimator=estimator)


def test_token_estimator_basic(estimator: TokenEstimator) -> None:
    # Empty string should return 0 tokens
    assert estimator.estimate_tokens("") == 0
    assert estimator.estimate_tokens(None) == 0

    # Simple text estimation should yield positive tokens
    text = "Hello, world! This is a unit test for token estimation."
    tokens = estimator.estimate_tokens(text)
    assert tokens > 0

    # Fallback to character counts works or standard tiktoken proxy
    assert estimator.is_within_budget(text, 100) is True
    assert estimator.is_within_budget(text, 2) is False


def test_token_estimator_truncation(estimator: TokenEstimator) -> None:
    text = "One two three four five six seven eight nine ten"
    tokens = estimator.estimate_tokens(text)

    # Truncate to less tokens should return a shorter string
    truncated = estimator.truncate_to_budget(text, tokens - 2)
    assert estimator.estimate_tokens(truncated) <= tokens - 2
    assert len(truncated) < len(text)

    # Truncating with large budget should keep whole text
    assert estimator.truncate_to_budget(text, 100) == text

    # Zero budget returns empty string
    assert estimator.truncate_to_budget(text, 0) == ""


def test_semantic_chunker_basic(chunker: SemanticChunker) -> None:
    # Empty inputs yield empty chunks
    assert chunker.split_text("") == []
    assert chunker.split_text(None) == []

    # Small text within budget yields a single chunk
    text = "Short text block."
    chunks = chunker.split_text(text, max_chunk_tokens=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_semantic_chunker_paragraph_split(chunker: SemanticChunker) -> None:
    # Text with natural paragraph breaks
    p1 = "Paragraph number one. It is relatively short but complete."
    p2 = "Paragraph number two. It adds some context to the test run."
    p3 = "Paragraph number three. This represents the final segment."
    full_text = f"{p1}\n\n{p2}\n\n{p3}"

    # Target max tokens low enough to force splits along double-newlines
    max_tokens = 15  # Should fit approx one paragraph
    chunks = chunker.split_text(full_text, max_chunk_tokens=max_tokens, chunk_overlap_tokens=0)

    # Should split into at least 3 distinct chunks corresponding to the paragraphs
    assert len(chunks) >= 3
    # Check that individual chunks are strictly under budget limits
    for chunk in chunks:
        assert chunker.estimator.estimate_tokens(chunk) <= max_tokens


def test_semantic_chunker_overlap(chunker: SemanticChunker) -> None:
    p1 = "This is the first segment of text that we are parsing."
    p2 = "This is the second segment of text that is longer."
    full_text = f"{p1}\n\n{p2}"

    # Lower budget to trigger split
    chunks = chunker.split_text(full_text, max_chunk_tokens=20, chunk_overlap_tokens=8)

    assert len(chunks) >= 2
    # The second chunk should contain some overlap text from the first chunk
    assert "parsing" in chunks[1] or "segment" in chunks[1]
