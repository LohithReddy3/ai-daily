
from fastapi import APIRouter, HTTPException, Query
from ..services.trends import analyze_trends
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/trends",
    tags=["trends"]
)

@router.get("/")
async def get_trends(days: int = Query(7, ge=1, le=90)):
    """
    Get thematic trends for the last X days.
    """
    try:
        trends = await analyze_trends(days=days)
        return trends
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universe")
async def get_universe_data(limit: int = Query(3600, ge=100, le=5000)):
    """
    Get raw items for the 'Data Universe' background visualization.
    """
    from ..services.trends import get_universe_items
    try:
        items = await get_universe_items(limit=limit)
        return {"items": items}
    except Exception as e:
        logger.error(f"Error fetching universe data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
