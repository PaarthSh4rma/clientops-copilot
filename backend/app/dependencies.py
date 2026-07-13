from fastapi import Request


def get_storage(request: Request):
    return request.app.state.storage


def get_embeddings(request: Request):
    return request.app.state.embeddings


def get_vector_store(request: Request):
    return request.app.state.vector_store


def get_llm(request: Request):
    return request.app.state.llm


def get_app_settings(request: Request):
    return request.app.state.settings
