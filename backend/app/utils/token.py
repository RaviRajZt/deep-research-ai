from __future__ import annotations

import structlog
import tiktoken

logger = structlog.get_logger(__name__)


class TokenEstimator:
    """Utility class to estimate and manage token budgets using tiktoken."""

    def __init__(self, default_encoding: str = "cl100k_base"):
        """Initialize the token estimator with a default encoding model.

        Modern models (like GPT-4, Grok, and Claude) use cl100k_base or o200k_base.
        For general purpose local estimation, cl100k_base serves as an excellent proxy.
        """
        self.default_encoding = default_encoding
        try:
            self._encoding = tiktoken.get_encoding(default_encoding)
            logger.debug("TokenEstimator initialized with encoding", encoding=default_encoding)
        except Exception as e:
            logger.warning(
                "Failed to load tiktoken encoding, falling back to char estimation",
                encoding=default_encoding,
                error=str(e),
            )
            self._encoding = None

    def estimate_tokens(self, text: str, model_or_encoding: str | None = None) -> int:
        """Estimate the number of tokens in the given text string.

        If tiktoken encoding fails or is missing, falls back to a standard
        character ratio estimation (approx 4 characters per token).
        """
        if not text:
            return 0

        # Try to get the specific model encoding if provided
        encoding = self._encoding
        if model_or_encoding:
            try:
                if model_or_encoding.startswith("gpt-") or "grok" in model_or_encoding:
                    encoding = tiktoken.encoding_for_model(model_or_encoding)
                else:
                    encoding = tiktoken.get_encoding(model_or_encoding)
            except Exception:
                # Keep default encoding if spec fails
                pass

        if encoding:
            try:
                return len(encoding.encode(text, disallowed_special=()))
            except Exception as e:
                logger.error("Error encoding text with tiktoken", error=str(e))

        # Safe fallback: ~4 characters per token
        return max(1, len(text) // 4)

    def is_within_budget(
        self, text: str, token_budget: int, model_or_encoding: str | None = None
    ) -> bool:
        """Check if the given text is within the specified token budget."""
        token_count = self.estimate_tokens(text, model_or_encoding)
        return token_count <= token_budget

    def truncate_to_budget(
        self, text: str, token_budget: int, model_or_encoding: str | None = None
    ) -> str:
        """Truncate the given text so its token count is strictly <= token_budget.

        Uses binary search over string indices to find the optimal truncation point.
        """
        if not text or token_budget <= 0:
            return ""

        token_count = self.estimate_tokens(text, model_or_encoding)
        if token_count <= token_budget:
            return text

        # Binary search for exact truncation point
        low = 0
        high = len(text)
        best_prefix = ""

        # Using tiktoken encoding if available to do direct slice-encoding (highly optimized)
        encoding = self._encoding
        if model_or_encoding:
            try:
                encoding = tiktoken.get_encoding(model_or_encoding)
            except Exception:
                try:
                    encoding = tiktoken.encoding_for_model(model_or_encoding)
                except Exception:
                    pass

        if encoding:
            try:
                tokens = encoding.encode(text, disallowed_special=())
                truncated_tokens = tokens[:token_budget]
                return encoding.decode(truncated_tokens)
            except Exception as e:
                logger.error("Tiktoken token slicing failed, falling back to binary search", error=str(e))

        # Binary search fallback
        while low <= high:
            mid = (low + high) // 2
            prefix = text[:mid]
            mid_tokens = self.estimate_tokens(prefix, model_or_encoding)

            if mid_tokens <= token_budget:
                best_prefix = prefix
                low = mid + 1  # Try to take more text
            else:
                high = mid - 1  # Need to take less text

        return best_prefix
