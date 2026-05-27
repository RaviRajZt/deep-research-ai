from __future__ import annotations

import re
import structlog
from app.utils.token import TokenEstimator

logger = structlog.get_logger(__name__)


class SemanticChunker:
    """Recursively splits raw text along semantic boundaries keeping within token constraints."""

    def __init__(self, token_estimator: TokenEstimator | None = None):
        """Initialize the semantic chunker with a token estimator."""
        self.estimator = token_estimator or TokenEstimator()

    def split_text(
        self,
        text: str,
        max_chunk_tokens: int = 2000,
        chunk_overlap_tokens: int = 200,
        model_or_encoding: str | None = None,
    ) -> list[str]:
        """Split text into chunks that are strictly within token and overlap constraints.

        Employs recursive splitting based on semantic boundaries:
        1. Paragraphs (\\n\\n)
        2. Lines (\\n)
        3. Sentences (using regex split on period/question/exclamation followed by space)
        4. Words (space ' ')
        5. Characters (absolute fallback)
        """
        if not text:
            return []

        if max_chunk_tokens <= 0:
            raise ValueError("max_chunk_tokens must be greater than 0")

        if chunk_overlap_tokens >= max_chunk_tokens:
            logger.warning(
                "chunk_overlap_tokens is >= max_chunk_tokens. Setting overlap to 10% of max.",
                overlap=chunk_overlap_tokens,
                max=max_chunk_tokens,
            )
            chunk_overlap_tokens = max_chunk_tokens // 10

        return self._recursive_split(
            text=text,
            separators=["\n\n", "\n", r"(?<=[.!?])\s+", " ", ""],
            max_tokens=max_chunk_tokens,
            overlap_tokens=chunk_overlap_tokens,
            model_or_encoding=model_or_encoding,
        )

    def _recursive_split(
        self,
        text: str,
        separators: list[str],
        max_tokens: int,
        overlap_tokens: int,
        model_or_encoding: str | None = None,
    ) -> list[str]:
        """Core recursive splitting method using a list of cascading separators."""
        # Calculate current token count
        total_tokens = self.estimator.estimate_tokens(text, model_or_encoding)
        if total_tokens <= max_tokens:
            return [text]

        # Find the first separator that actually splits the text
        if not separators:
            # If no separators left and still too large, we must truncate or slice by character count
            logger.debug(
                "No separators left, forcefully slicing text block",
                text_len=len(text),
                tokens=total_tokens,
            )
            return self._slice_forcefully(text, max_tokens, overlap_tokens, model_or_encoding)

        separator = separators[0]
        next_separators = separators[1:]

        # Split text by separator
        if separator == "":
            splits = list(text)
        elif separator.startswith("(?<="):  # regex lookbehind split (e.g. sentence boundary)
            splits = re.split(separator, text)
        else:
            splits = text.split(separator)

        # Filter out empty splits
        splits = [s for s in splits if s]
        if not splits:
            return []

        # If splitting doesn't produce multiple elements, move to the next separator
        if len(splits) == 1:
            return self._recursive_split(
                text=splits[0],
                separators=next_separators,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                model_or_encoding=model_or_encoding,
            )

        # Merge splits into chunks within token budget limits
        chunks: list[str] = []
        current_splits: list[str] = []
        current_tokens = 0

        # Re-attach split boundary markers depending on the separator type
        for split in splits:
            # Estimate tokens for this split
            split_tokens = self.estimator.estimate_tokens(split, model_or_encoding)

            # If a single split is larger than max_tokens, recursively split it using next separators
            if split_tokens > max_tokens:
                # Merge whatever we accumulated before splitting this giant block
                if current_splits:
                    chunks.append(separator.join(current_splits))
                    current_splits = []
                    current_tokens = 0

                sub_chunks = self._recursive_split(
                    text=split,
                    separators=next_separators,
                    max_tokens=max_tokens,
                    overlap_tokens=overlap_tokens,
                    model_or_encoding=model_or_encoding,
                )
                chunks.extend(sub_chunks)
                continue

            # If adding this split exceeds budget, finalize the current chunk
            if current_tokens + split_tokens > max_tokens:
                chunks.append(separator.join(current_splits))

                # Handle overlap: backtrack splits to build the overlap segment for the next chunk
                overlap_splits: list[str] = []
                overlap_accumulated_tokens = 0
                for s in reversed(current_splits):
                    s_tokens = self.estimator.estimate_tokens(s, model_or_encoding)
                    if overlap_accumulated_tokens + s_tokens <= overlap_tokens:
                        overlap_splits.insert(0, s)
                        overlap_accumulated_tokens += s_tokens
                    else:
                        break

                current_splits = overlap_splits
                current_tokens = overlap_accumulated_tokens

            # Append the current split
            current_splits.append(split)
            current_tokens += split_tokens

        # Add the trailing splits as the final chunk
        if current_splits:
            chunks.append(separator.join(current_splits))

        return [c for c in chunks if c.strip()]

    def _slice_forcefully(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int,
        model_or_encoding: str | None = None,
    ) -> list[str]:
        """Fallback slicing using binary search token estimation for safe chunks when splits fail."""
        chunks: list[str] = []
        remaining_text = text

        while remaining_text:
            # Estimate tokens of the remaining block
            rem_tokens = self.estimator.estimate_tokens(remaining_text, model_or_encoding)
            if rem_tokens <= max_tokens:
                chunks.append(remaining_text)
                break

            # Find exact character prefix matching max_tokens budget
            chunk_prefix = self.estimator.truncate_to_budget(
                remaining_text, max_tokens, model_or_encoding
            )
            if not chunk_prefix:
                # Absolute boundary safeguard to prevent infinite loops
                chunk_prefix = remaining_text[:max_tokens * 4]

            chunks.append(chunk_prefix)

            # Move cursor forward, taking overlap into account
            if overlap_tokens > 0:
                overlap_prefix = self.estimator.truncate_to_budget(
                    chunk_prefix[::-1], overlap_tokens, model_or_encoding
                )[::-1]
                remaining_text = remaining_text[len(chunk_prefix) - len(overlap_prefix) :]
            else:
                remaining_text = remaining_text[len(chunk_prefix) :]

        return chunks
