class ProviderError(RuntimeError):
    """An external provider could not complete an operation."""


class IngestionError(ValueError):
    """An uploaded document could not be safely ingested."""


class DuplicateDocumentError(IngestionError):
    def __init__(self, document_id: str, filename: str):
        self.document_id = document_id
        self.filename = filename
        super().__init__(f'This file is already indexed as "{filename}"')
