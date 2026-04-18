from fastapi import FastAPI, Query

from defi_pulse.analytics import (
    DEFAULT_BUFFER_BPS,
    DEFAULT_CAPITAL,
    DEFAULT_HEDGE_RATIO,
    CalculatorResult,
    OpportunitiesResponse,
    RatesResponse,
    SummaryResponse,
    build_calculator,
    build_opportunities_response,
    build_rates_response,
    build_summary,
)

app = FastAPI(title="Base DeFi Pulse", version="0.2.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "defi_pulse"}


@app.get("/api/summary", response_model=SummaryResponse)
def summary(
    capital: float = Query(DEFAULT_CAPITAL, gt=0),
    hedge_ratio: float = Query(DEFAULT_HEDGE_RATIO, gt=0, le=1),
    operational_buffer_bps: int = Query(DEFAULT_BUFFER_BPS, ge=0, le=500),
) -> SummaryResponse:
    return build_summary(
        capital=capital,
        hedge_ratio=hedge_ratio,
        operational_buffer_bps=operational_buffer_bps,
    )


@app.get("/api/rates", response_model=RatesResponse)
def rates() -> RatesResponse:
    return build_rates_response()


@app.get("/api/opportunities", response_model=OpportunitiesResponse)
def opportunities(
    capital: float = Query(DEFAULT_CAPITAL, gt=0),
    hedge_ratio: float = Query(DEFAULT_HEDGE_RATIO, gt=0, le=1),
    operational_buffer_bps: int = Query(DEFAULT_BUFFER_BPS, ge=0, le=500),
) -> OpportunitiesResponse:
    return build_opportunities_response(
        capital=capital,
        hedge_ratio=hedge_ratio,
        operational_buffer_bps=operational_buffer_bps,
    )


@app.get("/api/calculator", response_model=CalculatorResult)
def calculator(
    capital: float = Query(DEFAULT_CAPITAL, gt=0),
    hedge_ratio: float = Query(DEFAULT_HEDGE_RATIO, gt=0, le=1),
    operational_buffer_bps: int = Query(DEFAULT_BUFFER_BPS, ge=0, le=500),
    protocol: str | None = Query(None),
) -> CalculatorResult:
    return build_calculator(
        capital=capital,
        hedge_ratio=hedge_ratio,
        operational_buffer_bps=operational_buffer_bps,
        protocol=protocol,
    )
