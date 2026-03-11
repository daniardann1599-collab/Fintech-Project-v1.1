from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.market.market_data_service import get_bist100_snapshots, get_sp500_snapshots
from app.models.entities import User

logger = get_logger("banking.market_routes")

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/sp500")
def sp500_market_data(current_user: User = Depends(get_current_user)) -> list[dict]:
    try:
        return get_sp500_snapshots()
    except Exception as exc:
        logger.exception(
            "market.sp500.failed",
            extra={"extra_fields": {"user_id": current_user.id}},
        )
        raise HTTPException(status_code=502, detail="Market data unavailable") from exc


@router.get("/bist100")
def bist100_market_data(current_user: User = Depends(get_current_user)) -> list[dict]:
    try:
        return get_bist100_snapshots()
    except Exception as exc:
        logger.exception(
            "market.bist100.failed",
            extra={"extra_fields": {"user_id": current_user.id}},
        )
        raise HTTPException(status_code=502, detail="Market data unavailable") from exc
