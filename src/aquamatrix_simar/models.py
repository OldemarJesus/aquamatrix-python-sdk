"""Stable domain models mapped from Aquamatrix responses."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Invoice:
    """An invoice from the SIMAR billing history."""

    document_number: str
    document_type: str
    year: int
    issue_date: date
    payment_until: date
    amount: Decimal
    state: str
    payment_date: date | None
    client_code: str | None = None

    @property
    def is_pending(self) -> bool:
        """Whether the invoice has not been marked as paid by Aquamatrix."""
        return self.payment_date is None and self.state.casefold() in {
            "em cobrança",
            "pendente",
            "por pagar",
        }


@dataclass(frozen=True, slots=True)
class ReadingInfo:
    """The most recent meter reading reported by SIMAR."""

    reading_date: date
    reading_type: str
    value: str


@dataclass(frozen=True, slots=True)
class NextReadingsInfo:
    """Scheduled dates for company and customer readings."""

    company_date: date
    client_date: date


@dataclass(frozen=True, slots=True)
class GraphValue:
    """A labeled monetary value returned by a SIMAR billing graph."""

    label: str
    value: Decimal
    value_display: str | None = None