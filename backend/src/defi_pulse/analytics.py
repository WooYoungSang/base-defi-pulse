from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from statistics import mean
from typing import Literal

from pydantic import BaseModel

DEFAULT_CAPITAL = 100_000.0
DEFAULT_HEDGE_RATIO = 0.6
DEFAULT_BUFFER_BPS = 25


class CexRate(BaseModel):
    venue: str
    instrument: str
    funding_bps_8h: float
    funding_apy: float
    basis_apy: float
    carry_apy: float
    note: str


class BaseRate(BaseModel):
    protocol: str
    strategy: str
    supply_apy: float
    incentive_apy: float
    borrow_cost_apy: float
    net_apy: float
    liquidity_musd: float
    risk: Literal["low", "medium", "high"]
    note: str


class TrendPoint(BaseModel):
    day: date
    cex_carry_apy: float
    base_net_apy: float
    divergence_apy: float


class Opportunity(BaseModel):
    protocol: str
    strategy: str
    risk: Literal["low", "medium", "high"]
    liquidity_musd: float
    edge_apy: float
    adjusted_edge_apy: float
    projected_monthly_edge_usd: float
    confidence: Literal["high", "medium", "low"]
    action: str
    rationale: str


class CalculatorResult(BaseModel):
    selected_protocol: str
    cex_benchmark: str
    capital_usd: float
    hedge_ratio: float
    operational_buffer_bps: int
    deployable_capital_usd: float
    gross_monthly_edge_usd: float
    monthly_buffer_cost_usd: float
    net_monthly_edge_usd: float
    break_even_days: int | None


class Snapshot(BaseModel):
    mean_cex_carry_apy: float
    mean_base_net_apy: float
    divergence_apy: float
    divergence_score: int
    regime: str
    top_protocol: str
    top_adjusted_edge_apy: float


class RatesResponse(BaseModel):
    data_mode: Literal["curated-fallback"]
    generated_at: datetime
    benchmark: str
    averages: dict[str, float]
    cex: list[CexRate]
    base: list[BaseRate]


class OpportunitiesResponse(BaseModel):
    data_mode: Literal["curated-fallback"]
    generated_at: datetime
    benchmark: str
    capital_usd: float
    hedge_ratio: float
    operational_buffer_bps: int
    opportunities: list[Opportunity]


class SummaryResponse(BaseModel):
    project: str
    data_mode: Literal["curated-fallback"]
    updated_at: datetime
    snapshot: Snapshot
    trend: list[TrendPoint]
    top_opportunity: Opportunity
    calculator_preview: CalculatorResult
    assumptions: list[str]


_RAW_CEX = [
    {
        "venue": "Binance",
        "instrument": "ETH-PERP",
        "funding_bps_8h": 0.45,
        "basis_apy": 2.6,
        "note": "Funding cooled after CPI week; carry now driven more by basis than perp imbalance.",
    },
    {
        "venue": "Bybit",
        "instrument": "ETH-PERP",
        "funding_bps_8h": 0.62,
        "basis_apy": 3.1,
        "note": "Higher retail leverage keeps basis elevated, but not enough to dominate Base lending yields.",
    },
    {
        "venue": "OKX",
        "instrument": "ETH-PERP",
        "funding_bps_8h": 0.28,
        "basis_apy": 2.2,
        "note": "Most conservative venue in the basket; useful as a lower-bound carry benchmark.",
    },
]

_RAW_BASE = [
    {
        "protocol": "Morpho Blue",
        "strategy": "cbBTC collateral / USDC lending loop",
        "supply_apy": 11.2,
        "incentive_apy": 1.6,
        "borrow_cost_apy": 0.2,
        "liquidity_musd": 410,
        "risk": "low",
        "note": "Deep liquidity and predictable incentives make this the cleanest institutional carry leg on Base.",
    },
    {
        "protocol": "Moonwell",
        "strategy": "USDC supply with WELL incentives",
        "supply_apy": 8.7,
        "incentive_apy": 1.3,
        "borrow_cost_apy": 0.1,
        "liquidity_musd": 265,
        "risk": "low",
        "note": "Lower headline APY, but stable utilization and good fit for treasury idle cash.",
    },
    {
        "protocol": "Aave v3",
        "strategy": "USDC supply with safety-first posture",
        "supply_apy": 7.9,
        "incentive_apy": 0.9,
        "borrow_cost_apy": 0.1,
        "liquidity_musd": 350,
        "risk": "low",
        "note": "Strongest risk-adjusted option when policy requires blue-chip venue selection.",
    },
    {
        "protocol": "Aerodrome",
        "strategy": "WETH/USDC concentrated LP",
        "supply_apy": 14.5,
        "incentive_apy": 4.8,
        "borrow_cost_apy": 3.7,
        "liquidity_musd": 140,
        "risk": "high",
        "note": "Highest raw yield in the basket, but LP inventory drift warrants a larger haircut.",
    },
    {
        "protocol": "Uniswap v3",
        "strategy": "cbBTC/WETH concentrated LP",
        "supply_apy": 11.8,
        "incentive_apy": 2.7,
        "borrow_cost_apy": 2.9,
        "liquidity_musd": 92,
        "risk": "medium",
        "note": "Good directional fit when you already hold beta and want fees to subsidize exposure.",
    },
]

_TREND_SERIES = [
    (0.9, 10.2),
    (1.1, 10.4),
    (1.0, 10.8),
    (0.7, 11.0),
    (0.6, 11.5),
    (0.4, 11.6),
    (0.5, 11.7),
]

_RISK_MULTIPLIER = {"low": 0.94, "medium": 0.82, "high": 0.68}


@lru_cache
def get_cex_rates() -> list[CexRate]:
    rates: list[CexRate] = []
    for row in _RAW_CEX:
        funding_apy = round(row["funding_bps_8h"] * 10.95, 2)
        carry_apy = round(funding_apy + row["basis_apy"], 2)
        rates.append(
            CexRate(
                venue=row["venue"],
                instrument=row["instrument"],
                funding_bps_8h=row["funding_bps_8h"],
                funding_apy=funding_apy,
                basis_apy=row["basis_apy"],
                carry_apy=carry_apy,
                note=row["note"],
            )
        )
    return rates


@lru_cache
def get_base_rates() -> list[BaseRate]:
    rates: list[BaseRate] = []
    for row in _RAW_BASE:
        net_apy = round(row["supply_apy"] + row["incentive_apy"] - row["borrow_cost_apy"], 2)
        rates.append(
            BaseRate(
                protocol=row["protocol"],
                strategy=row["strategy"],
                supply_apy=row["supply_apy"],
                incentive_apy=row["incentive_apy"],
                borrow_cost_apy=row["borrow_cost_apy"],
                net_apy=net_apy,
                liquidity_musd=row["liquidity_musd"],
                risk=row["risk"],
                note=row["note"],
            )
        )
    return rates


@lru_cache
def benchmark_name() -> str:
    venues = ", ".join(rate.venue for rate in get_cex_rates())
    return f"Mean CEX carry ({venues})"


@lru_cache
def mean_cex_carry() -> float:
    return round(mean(rate.carry_apy for rate in get_cex_rates()), 2)


@lru_cache
def mean_base_net() -> float:
    return round(mean(rate.net_apy for rate in get_base_rates()), 2)


@lru_cache
def build_trend() -> list[TrendPoint]:
    today = datetime.now(timezone.utc).date()
    trend: list[TrendPoint] = []
    cex_mean = mean_cex_carry()
    base_mean = mean_base_net()
    for index, (cex_offset, base_offset) in enumerate(_TREND_SERIES):
        cex_value = round(cex_mean - cex_offset, 2)
        base_value = round(base_mean - base_offset, 2)
        trend.append(
            TrendPoint(
                day=today - timedelta(days=len(_TREND_SERIES) - index - 1),
                cex_carry_apy=cex_value,
                base_net_apy=base_value,
                divergence_apy=round(base_value - cex_value, 2),
            )
        )
    return trend


@lru_cache
def build_snapshot() -> Snapshot:
    divergence = round(mean_base_net() - mean_cex_carry(), 2)
    score = max(0, min(100, round(50 + divergence * 8)))
    if divergence >= 4:
        regime = "base-yield-dominant"
    elif divergence >= 1.5:
        regime = "base-yield-favored"
    elif divergence <= -2:
        regime = "cex-carry-dominant"
    else:
        regime = "balanced"

    top = build_opportunities()[0]
    return Snapshot(
        mean_cex_carry_apy=mean_cex_carry(),
        mean_base_net_apy=mean_base_net(),
        divergence_apy=divergence,
        divergence_score=score,
        regime=regime,
        top_protocol=top.protocol,
        top_adjusted_edge_apy=top.adjusted_edge_apy,
    )


@lru_cache
def build_rates_response() -> RatesResponse:
    return RatesResponse(
        data_mode="curated-fallback",
        generated_at=datetime.now(timezone.utc),
        benchmark=benchmark_name(),
        averages={
            "cex_carry_apy": mean_cex_carry(),
            "base_net_apy": mean_base_net(),
            "divergence_apy": round(mean_base_net() - mean_cex_carry(), 2),
        },
        cex=get_cex_rates(),
        base=get_base_rates(),
    )


@lru_cache
def build_opportunities() -> list[Opportunity]:
    benchmark = mean_cex_carry()
    default_deployable_capital = DEFAULT_CAPITAL * DEFAULT_HEDGE_RATIO
    opportunities: list[Opportunity] = []
    for rate in get_base_rates():
        edge_apy = round(rate.net_apy - benchmark, 2)
        adjusted_edge = round(max(edge_apy, 0) * _RISK_MULTIPLIER[rate.risk], 2)
        gross_monthly = round(default_deployable_capital * adjusted_edge / 100 / 12, 2)

        confidence: Literal["high", "medium", "low"]
        if rate.risk == "low" and rate.liquidity_musd >= 250:
            confidence = "high"
        elif rate.risk == "high" or rate.liquidity_musd < 120:
            confidence = "low"
        else:
            confidence = "medium"

        opportunities.append(
            Opportunity(
                protocol=rate.protocol,
                strategy=rate.strategy,
                risk=rate.risk,
                liquidity_musd=rate.liquidity_musd,
                edge_apy=edge_apy,
                adjusted_edge_apy=adjusted_edge,
                projected_monthly_edge_usd=gross_monthly,
                confidence=confidence,
                action=f"Rotate delta-neutral carry into {rate.protocol} and monitor liquidity utilization.",
                rationale=(
                    f"{rate.protocol} delivers {rate.net_apy:.2f}% net APY versus {benchmark:.2f}% "
                    f"mean off-chain carry, leaving a {edge_apy:.2f}% gross edge before policy haircuts."
                ),
            )
        )

    return sorted(
        opportunities,
        key=lambda item: (item.adjusted_edge_apy, item.liquidity_musd, item.edge_apy),
        reverse=True,
    )


@lru_cache
def build_opportunities_response(
    capital: float = DEFAULT_CAPITAL,
    hedge_ratio: float = DEFAULT_HEDGE_RATIO,
    operational_buffer_bps: int = DEFAULT_BUFFER_BPS,
) -> OpportunitiesResponse:
    opportunities = [
        opportunity.model_copy(
            update={
                "projected_monthly_edge_usd": round(
                    capital * hedge_ratio * opportunity.adjusted_edge_apy / 100 / 12
                    - capital * operational_buffer_bps / 10_000 / 12,
                    2,
                )
            }
        )
        for opportunity in build_opportunities()
    ]
    return OpportunitiesResponse(
        data_mode="curated-fallback",
        generated_at=datetime.now(timezone.utc),
        benchmark=benchmark_name(),
        capital_usd=capital,
        hedge_ratio=hedge_ratio,
        operational_buffer_bps=operational_buffer_bps,
        opportunities=opportunities,
    )


def build_calculator(
    *,
    capital: float = DEFAULT_CAPITAL,
    hedge_ratio: float = DEFAULT_HEDGE_RATIO,
    operational_buffer_bps: int = DEFAULT_BUFFER_BPS,
    protocol: str | None = None,
) -> CalculatorResult:
    opportunities = build_opportunities()
    selected = opportunities[0]
    if protocol is not None:
        selected = next((item for item in opportunities if item.protocol == protocol), selected)

    deployable_capital = round(capital * hedge_ratio, 2)
    gross_monthly = round(deployable_capital * selected.adjusted_edge_apy / 100 / 12, 2)
    monthly_buffer_cost = round(capital * operational_buffer_bps / 10_000 / 12, 2)
    net_monthly = round(gross_monthly - monthly_buffer_cost, 2)
    if gross_monthly <= 0:
        break_even_days = None
    else:
        break_even_days = max(1, round(monthly_buffer_cost / (gross_monthly / 30)))

    return CalculatorResult(
        selected_protocol=selected.protocol,
        cex_benchmark=benchmark_name(),
        capital_usd=capital,
        hedge_ratio=hedge_ratio,
        operational_buffer_bps=operational_buffer_bps,
        deployable_capital_usd=deployable_capital,
        gross_monthly_edge_usd=gross_monthly,
        monthly_buffer_cost_usd=monthly_buffer_cost,
        net_monthly_edge_usd=net_monthly,
        break_even_days=break_even_days,
    )


def build_summary(
    *,
    capital: float = DEFAULT_CAPITAL,
    hedge_ratio: float = DEFAULT_HEDGE_RATIO,
    operational_buffer_bps: int = DEFAULT_BUFFER_BPS,
) -> SummaryResponse:
    opportunities = build_opportunities()
    return SummaryResponse(
        project="Base DeFi Pulse",
        data_mode="curated-fallback",
        updated_at=datetime.now(timezone.utc),
        snapshot=build_snapshot(),
        trend=build_trend(),
        top_opportunity=opportunities[0],
        calculator_preview=build_calculator(
            capital=capital,
            hedge_ratio=hedge_ratio,
            operational_buffer_bps=operational_buffer_bps,
        ),
        assumptions=[
            "Uses curated fallback data until live exchange and Base protocol connectors are wired in.",
            "Funding APY annualizes the latest 8h funding snapshot without leverage or fee rebates.",
            "Base net APY equals supply yield plus incentives minus explicit borrow or hedging costs.",
            "Operational buffer models execution slippage, gas, custody, and treasury policy overhead.",
        ],
    )
