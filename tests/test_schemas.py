import pytest
from pydantic import ValidationError

from app.accounts.schemas import AccountCreateRequest
from app.transfers.schemas import TransferInitiateRequest


def test_account_currency_is_normalized_to_uppercase() -> None:
    payload = AccountCreateRequest(customer_id=1, currency="usd")

    assert payload.currency == "USD"


def test_account_currency_validation_rejects_non_iso_letters() -> None:
    with pytest.raises(ValidationError):
        AccountCreateRequest(customer_id=1, currency="u1d")


def test_transfer_initiate_requires_positive_amount() -> None:
    with pytest.raises(ValidationError):
        TransferInitiateRequest(from_account=1, to_account=2, amount=0)
