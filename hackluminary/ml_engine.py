"""Backward-compatible shim for deprecated v1 ML engine API."""

from __future__ import annotations


class MLEngine:
    """Compatibility wrapper.

    v2 uses `hackluminary.ai_pipeline` with local llama.cpp models.
    This class remains to avoid import breakage for older integrations.
    """

    def __init__(self):
        self.generator = None

    def enhance_docs(self, doc_data, code_analysis):
        _ = code_analysis
        # No-op in v2. Keep deterministic source-of-truth from docs/analyzer.
        return doc_data
