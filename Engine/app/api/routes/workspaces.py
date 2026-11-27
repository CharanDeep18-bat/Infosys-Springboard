"""API Routes: Workspaces and Research Sessions Management."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies.auth import get_current_user
from app.infrastructure.database import get_database_repository
from app.schemas.workspace import (
    ResearchSessionCreate,
    ResearchSessionResponse,
    WorkspaceCreate,
    WorkspaceResponse,
)

router = APIRouter(tags=["Workspaces & Sessions"])

@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    payload: WorkspaceCreate,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    created = repo.create_user_workspace(
        user_id=user["id"],
        name=payload.name,
        description=payload.description
    )

    return WorkspaceResponse(**created)

@router.get("/workspaces", response_model=List[WorkspaceResponse])
def list_workspaces(
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    workspaces = repo.list_user_workspaces(
        user_id=user["id"]
    )

    return [WorkspaceResponse(**w) for w in workspaces]

@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    ws = repo.get_user_workspace(
        workspace_id=workspace_id,
        user_id=user["id"]
    )

    if not ws:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return WorkspaceResponse(**ws)

# @router.post("/workspaces/{workspace_id}/sessions", response_model=ResearchSessionResponse, status_code=201)
# def create_session(workspace_id: str, payload: ResearchSessionCreate):
#     """Create a new research session inside a workspace."""
#     repo = get_database_repository()
#     ws = repo.get_workspace(workspace_id)
#     if not ws:
#         if workspace_id == "default-workspace":
#             ws = repo.create_workspace(
#                 name="Default Workspace",
#                 description="Default institutional research workspace",
#                 workspace_id="default-workspace",
#             )
#         else:
#             raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found.")

#     session = repo.create_session(
#         workspace_id=workspace_id,
#         title=payload.title,
#         description=payload.description,
#     )
#     return ResearchSessionResponse(**session)


# @router.get("/workspaces/{workspace_id}/sessions", response_model=List[ResearchSessionResponse])
# def list_workspace_sessions(workspace_id: str):
#     """List all research sessions within a workspace."""
#     repo = get_database_repository()
#     ws = repo.get_workspace(workspace_id)
#     if not ws:
#         if workspace_id == "default-workspace":
#             ws = repo.create_workspace(
#                 name="Default Workspace",
#                 description="Default institutional research workspace",
#                 workspace_id="default-workspace",
#             )
#         else:
#             raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found.")

#     sessions = repo.list_sessions(workspace_id=workspace_id)
#     return [ResearchSessionResponse(**s) for s in sessions]


# @router.get("/sessions/{session_id}", response_model=ResearchSessionResponse)
# def get_session(session_id: str):
#     """Get research session details by ID, including assigned document IDs."""
#     repo = get_database_repository()
#     session = repo.get_session(session_id)
#     if not session:
#         raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
#     return ResearchSessionResponse(**session)
@router.post(
    "/workspaces/{workspace_id}/sessions",
    response_model=ResearchSessionResponse,
    status_code=201
)
def create_session(
    workspace_id: str,
    payload: ResearchSessionCreate,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    try:
        session = repo.create_user_session(
            workspace_id=workspace_id,
            user_id=user["id"],
            title=payload.title,
            description=payload.description
        )
        repo.update_user_session_metadata(
            session["session_id"],
            user["id"],
            payload.metadata
        )

        session = repo.get_user_session(
            session["session_id"],
            user["id"]
        )
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return ResearchSessionResponse(**session)
@router.get(
    "/workspaces/{workspace_id}/sessions",
    response_model=List[ResearchSessionResponse]
)
def list_workspace_sessions(
    workspace_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    workspace = repo.get_user_workspace(
        workspace_id=workspace_id,
        user_id=user["id"]
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    sessions = repo.list_user_sessions(
        workspace_id=workspace_id,
        user_id=user["id"]
    )

    return [
        ResearchSessionResponse(**s)
        for s in sessions
    ]


@router.post(
    "/workspaces/default",
    response_model=WorkspaceResponse
)
def get_default_workspace(
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    return WorkspaceResponse(
        **repo.get_or_create_default_workspace(
            user_id=user["id"]
        )
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ResearchSessionResponse
)
def get_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    repo = get_database_repository()

    session = repo.get_user_session(
        session_id=session_id,
        user_id=user["id"]
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return ResearchSessionResponse(**session)



@router.patch(
    "/sessions/{session_id}",
    response_model=ResearchSessionResponse
)
def update_session(
    session_id: str,
    payload: ResearchSessionCreate,
    user: dict = Depends(get_current_user)
):

    repo = get_database_repository()

    try:
        session = repo.update_user_session(
            session_id=session_id,
            user_id=user["id"],
            title=payload.title,
            description=payload.description or ""
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )
    if "metadata" in payload.model_fields_set:

        repo.update_user_session_metadata(
            session_id,
            user["id"],
            payload.metadata
        )

        session = repo.get_user_session(
            session_id,
            user["id"]
        )
    return ResearchSessionResponse(**session)

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):

    repo = get_database_repository()

    try:
        deleted = repo.delete_user_session(
            session_id,
            user["id"]
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc)
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    return {
        "status": "deleted",
        "session_id": session_id
    }

@router.post(
    "/sessions/{session_id}/duplicate",
    response_model=ResearchSessionResponse
)
def duplicate_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):

    repo = get_database_repository()

    session = repo.duplicate_user_session(
        session_id,
        user["id"]
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )

    return ResearchSessionResponse(**session)