from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.market.market_data_service import get_sp500_snapshots
from app.models.entities import User

logger = get_logger("banking.market_routes")

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/sp500")
def sp500_market_data(current_user: User = Depends(get_current_user)) -> list[dict]:
    try:
        return get_sp500_snapshots()
    except ValueError as exc:
        logger.warning(
            "market.sp500.config_error",
            extra={"extra_fields": {"user_id": current_user.id, "error": str(exc)}},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        logger.exception(
            "market.sp500.http_error",
            extra={
                "extra_fields": {
                    "user_id": current_user.id,
                    "status_code": exc.response.status_code,
                }
            },
        )
        raise HTTPException(
            status_code=502,
            detail=f"Finnhub market data error (HTTP {exc.response.status_code})",
        ) from exc
    except Exception as exc:
        logger.exception(
            "market.sp500.failed",
            extra={"extra_fields": {"user_id": current_user.id}},
        )
        raise HTTPException(status_code=502, detail="Market data unavailable") from exc
