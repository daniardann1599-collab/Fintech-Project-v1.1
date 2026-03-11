from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.loans.schemas import LoanRequest, LoanResponse, LoanStatusUpdate
from app.loans.service import request_loan, update_loan_status
from app.models.entities import Loan, User

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan_request(
    payload: LoanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoanResponse:
    try:
        loan = request_loan(db, current_user, payload.account_id, payload.amount, payload.currency, payload.purpose)
        db.commit()
        db.refresh(loan)
        return loan
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=list[LoanResponse])
def list_user_loans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LoanResponse]:
    return (
        db.query(Loan)
        .filter(Loan.user_id == current_user.id)
        .order_by(Loan.created_at.desc())
        .all()
    )


@router.get("/admin", response_model=list[LoanResponse])
def list_all_loans(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[LoanResponse]:
    return db.query(Loan).order_by(Loan.created_at.desc()).all()


@router.post("/{loan_id}/status", response_model=LoanResponse)
def update_status(
    loan_id: int,
    payload: LoanStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoanResponse:
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    try:
        loan = update_loan_status(db, loan, payload.status, current_user)
        db.commit()
        db.refresh(loan)
        return loan
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
