from app.integrations.vector_store import PineconeVectorStore


class IndexSpy:
    def __init__(self):
        self.kwargs = None

    def query(self, **kwargs):
        self.kwargs = kwargs
        return type("Result", (), {"matches": []})()

    def delete(self, **kwargs):
        self.delete_kwargs = kwargs


def test_pinecone_search_passes_document_filter():
    store = object.__new__(PineconeVectorStore)
    store._index = IndexSpy()
    store.search(document_id="document-b", query_vector=[0.1], top_k=3)
    assert store._index.kwargs["filter"] == {"document_id": {"$eq": "document-b"}}


def test_pinecone_delete_passes_document_filter():
    store = object.__new__(PineconeVectorStore)
    store._index = IndexSpy()
    store.delete_document("document-b")
    assert store._index.delete_kwargs == {"filter": {"document_id": {"$eq": "document-b"}}}
