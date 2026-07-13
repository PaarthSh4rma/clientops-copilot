class ProviderError(RuntimeError):
    """An external provider could not complete an operation."""


class IngestionError(ValueError):
    """An uploaded document could not be safely ingested."""
