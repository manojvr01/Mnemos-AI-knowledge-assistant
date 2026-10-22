from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.security.dependencies import get_current_user, get_current_workspace
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import VectorSearchService

router = APIRouter()


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def semantic_search(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic vector search across indexed documents within the active workspace.
    Optionally filters by collection_id and applies similarity thresholding.
    """
    search_service = VectorSearchService(db=db)
    results = await search_service.search(
        workspace_id=workspace.id,
        query=req.query,
        top_k=req.top_k,
        similarity_threshold=req.similarity_threshold,
        collection_id=req.collection_id,
        document_id=req.document_id,
    )

    return SearchResponse(
        query=req.query,
        workspace_id=workspace.id,
        total_results=len(results),
        results=results
    )
