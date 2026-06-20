import uuid

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_business_membership, get_stats_service
from app.models.business_member import BusinessMember
from app.schemas.stats import BusinessStatsRead
from app.services.stats import StatsService

router = APIRouter(
    prefix="/businesses/{business_id}/stats",
    tags=["stats"],
)


@router.get("", response_model=BusinessStatsRead, summary="Get dashboard statistics")
async def get_business_stats(
    business_id: uuid.UUID,
    _: BusinessMember = Depends(get_business_membership),
    stats_service: StatsService = Depends(get_stats_service),
    low_stock_limit: int = Query(default=50, ge=1, le=100),
) -> BusinessStatsRead:
    return await stats_service.get_business_stats(
        business_id=business_id,
        low_stock_limit=low_stock_limit,
    )
