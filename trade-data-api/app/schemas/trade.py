"""Pydantic schemas: request validation and response models."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Countries ---

class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    iso_alpha2: str
    iso_alpha3: str
    m49_code: int
    name: str
    region: str | None = None


# --- HS codes ---

class HSCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    level: int
    parent_code: str | None = None
    description: str
    short_name: str | None = None


class HSCodeDetail(HSCodeOut):
    """HS code with its hierarchy: ancestors and immediate children."""
    ancestors: list[HSCodeOut] = []
    children: list[HSCodeOut] = []


# --- Trade flows ---

class TradePartner(BaseModel):
    """One row in a 'top trading partners' response."""
    model_config = ConfigDict(from_attributes=True)
    country: CountryOut
    value_usd: float
    quantity: float | None = None
    quantity_unit: str | None = None
    rank: int


class TopPartnersResponse(BaseModel):
    hs_code: str
    hs_description: str
    flow_type: Literal["import", "export"]
    year: int
    reporter: CountryOut | None = None
    partners: list[TradePartner]


class TradeFlowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reporter: CountryOut
    partner: CountryOut
    hs_code: str
    year: int
    flow_type: str
    value_usd: float
    quantity: float | None = None
    quantity_unit: str | None = None
    source: str


class TradeTrendPoint(BaseModel):
    year: int
    value_usd: float
    quantity: float | None = None


class TradeTrendResponse(BaseModel):
    reporter: CountryOut
    partner: CountryOut
    hs_code: str
    hs_description: str
    flow_type: str
    points: list[TradeTrendPoint]
    total_value_usd: float
    growth_rate_pct: float | None = Field(
        None, description="CAGR % across the queried range, if >=2 points."
    )


# --- Tariffs ---

class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reporter: CountryOut
    partner: CountryOut | None = None
    hs_code: str
    year: int
    rate_type: str
    ad_valorem_rate: float | None = None
    specific_rate: str | None = None
    agreement: str | None = None
    notes: str | None = None


# --- Compliance ---

class ComplianceDocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_name: str
    issuing_authority: str | None = None
    description: str
    is_mandatory: bool
    reporter: CountryOut | None = None
    partner: CountryOut | None = None
    hs_code: str | None = None


class ComplianceResponse(BaseModel):
    corridor: str = Field(..., description="e.g. 'IN -> US'")
    hs_code: str | None = None
    documents: list[ComplianceDocOut]


# --- Errors / health ---

class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    data_mode: str
    db_ok: bool
    timestamp: datetime
