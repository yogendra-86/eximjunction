"""ORM models for the trade data domain.

Schema overview:

    Country (M49 + ISO codes)
        |
        +-- TradeFlow (reporter -> partner, by HS code, by year/month)
        |
        +-- Tariff (reporter applies rate to partner, by HS code)
        |
        +-- ComplianceDoc (corridor: reporter <-> partner, by HS code)

    HSCode (hierarchical: chapter -> heading -> subheading)
        ^
        +-- referenced by TradeFlow, Tariff, ComplianceDoc
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# Use BigInteger on Postgres but Integer on SQLite (for autoincrement support in tests).
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iso_alpha2: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    iso_alpha3: Mapped[str] = mapped_column(String(3), unique=True, index=True)
    m49_code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    region: Mapped[str | None] = mapped_column(String(80), nullable=True)


class HSCode(Base):
    """
    Harmonized System codes. Stored at all levels (2/4/6 digit) so the
    same table can support hierarchy queries.

    level: 2 = chapter, 4 = heading, 6 = subheading
    parent_code: NULL for chapters; the next level up otherwise.
    """
    __tablename__ = "hs_codes"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    parent_code: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("hs_codes.code"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    children = relationship("HSCode", backref="parent", remote_side=[code])

    __table_args__ = (
        Index("ix_hs_codes_description_lower", "description"),
    )


class TradeFlow(Base):
    """
    Aggregated trade flow record: how much value/quantity flowed from
    `partner` to `reporter` (or vice versa) for a given HS code in a year.

    flow_type: "import" or "export" (from the reporter's perspective)
    value_usd: trade value in USD
    quantity / quantity_unit: physical quantity, optional
    """
    __tablename__ = "trade_flows"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    hs_code: Mapped[str] = mapped_column(String(10), ForeignKey("hs_codes.code"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    flow_type: Mapped[str] = mapped_column(String(8))  # 'import' | 'export'
    value_usd: Mapped[float] = mapped_column(Float)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="seed")
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reporter = relationship("Country", foreign_keys=[reporter_id])
    partner = relationship("Country", foreign_keys=[partner_id])

    __table_args__ = (
        UniqueConstraint(
            "reporter_id", "partner_id", "hs_code", "year", "flow_type",
            name="uq_trade_flow",
        ),
        Index("ix_trade_flows_lookup", "hs_code", "flow_type", "year"),
    )


class Tariff(Base):
    """
    Tariff/duty rate that `reporter` applies to imports from `partner`
    for a given HS code. MFN rates use partner_id NULL.
    """
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id"), nullable=True, index=True
    )
    hs_code: Mapped[str] = mapped_column(String(10), ForeignKey("hs_codes.code"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    rate_type: Mapped[str] = mapped_column(String(20))  # 'MFN', 'preferential', 'bound'
    ad_valorem_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # percent
    specific_rate: Mapped[str | None] = mapped_column(String(120), nullable=True)
    agreement: Mapped[str | None] = mapped_column(String(80), nullable=True)  # e.g. "ASEAN-India FTA"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="seed")

    reporter = relationship("Country", foreign_keys=[reporter_id])
    partner = relationship("Country", foreign_keys=[partner_id])


class ComplianceDoc(Base):
    """
    Required documents / certifications for a trade corridor + product.

    Either reporter or partner can be NULL to mean "any"; this lets us
    encode general requirements (e.g. all imports need a commercial invoice)
    plus corridor- and product-specific ones (phytosanitary cert for
    agricultural exports from IN to EU).
    """
    __tablename__ = "compliance_docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id"), nullable=True, index=True
    )
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("countries.id"), nullable=True, index=True
    )
    hs_code: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("hs_codes.code"), nullable=True, index=True
    )
    document_name: Mapped[str] = mapped_column(String(160))
    issuing_authority: Mapped[str | None] = mapped_column(String(160), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    reporter = relationship("Country", foreign_keys=[reporter_id])
    partner = relationship("Country", foreign_keys=[partner_id])
