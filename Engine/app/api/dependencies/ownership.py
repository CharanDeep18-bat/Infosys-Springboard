from typing import List, Optional

from fastapi import HTTPException, Depends

from app.api.dependencies.auth import get_current_user
from app.infrastructure.database import get_database_repository


def require_owned_workspace(workspace_id: str, user_id: str):
    repo = get_database_repository()

    workspace = repo.get_user_workspace(
        workspace_id=workspace_id,
        user_id=user_id
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return workspace


def require_owned_session(session_id: str, user_id: str):
    repo = get_database_repository()

    session = repo.get_user_session(
        session_id=session_id,
        user_id=user_id
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return session


def require_owned_document(document_id: str, user_id: str):
    repo = get_database_repository()

    document = repo.get_user_document(
        document_id=document_id,
        user_id=user_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


def require_owned_documents(
    document_ids: List[str],
    user_id: str,
    workspace_id: Optional[str] = None
):
    if not document_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one document is required"
        )

    documents = []

    for document_id in dict.fromkeys(document_ids):

        document = require_owned_document(
            document_id=document_id,
            user_id=user_id
        )

        if workspace_id and document["workspace_id"] != workspace_id:
            raise HTTPException(
                status_code=404,
                detail="Document not found in workspace"
            )

        documents.append(document)

    return documents


def require_session_documents(
    session_id: str,
    document_ids: List[str],
    user_id: str
):
    session = require_owned_session(
        session_id=session_id,
        user_id=user_id
    )

    documents = require_owned_documents(
        document_ids=document_ids,
        user_id=user_id,
        workspace_id=session["workspace_id"]
    )

    allowed_ids = set(session.get("document_ids") or [])

    for document in documents:
        if document["document_id"] not in allowed_ids:
            raise HTTPException(
                status_code=404,
                detail="Document not found in session"
            )

    return documents


def get_owned_document(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    return require_owned_document(
        document_id=document_id,
        user_id=user["id"]
    )


def get_owned_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    return require_owned_session(
        session_id=session_id,
        user_id=user["id"]
    )