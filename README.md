# Base DeFi Pulse

Base DeFi Pulse compares ETH perp funding/basis on major CEX venues with Base-native yield opportunities, then ranks where treasury or delta-neutral capital can earn the strongest risk-adjusted edge.

## What is implemented

### S1 — curated rate engine
- Normalizes 8h funding into annualized CEX carry across Binance, Bybit, and OKX
- Models Base yield baskets across Morpho, Moonwell, Aave, Aerodrome, and Uniswap v3
- Produces a weekly divergence trend plus a ranked opportunity book with risk haircuts

### S2 — FastAPI control plane
- `GET /api/summary` — regime snapshot, trend, top opportunity, and calculator preview
- `GET /api/rates` — normalized CEX/Base baskets and benchmark averages
- `GET /api/opportunities` — ranked opportunity list with capital-aware monthly edge estimates
- `GET /api/calculator` — deployable-capital calculator for a selected protocol
- `GET /api/health` — service healthcheck
- `GET /api/connectors` — live connector stage status (Binance live funding + Base yield fallback)

### S3 — Next.js dashboard
- Live dashboard sections for CEX carry, Base yield basket, divergence trend, and ranked opportunities
- Interactive "Why Base" calculator for capital, hedge ratio, and operational buffer sensitivity
- Runtime fetches from the FastAPI backend with bundled fallback data so the UI still builds offline

## Data sources
- CEX carry basket: curated fallback snapshots for Binance, Bybit, and OKX ETH perp funding/basis
- Base yield basket: curated fallback snapshots for Morpho Blue, Moonwell, Aave v3, Aerodrome, and Uniswap v3
- Current mode stays deterministic until live connectors and persisted history are added

## Environment
- `NEXT_PUBLIC_API_URL` — frontend base URL for the FastAPI service (default `http://localhost:8000`)
- `DEFI_PULSE_ENABLE_LIVE` — set to `1` to fetch live Binance premium index snapshots
- `DEFI_PULSE_BINANCE_PREMIUM_INDEX_URL` — override the Binance premium index endpoint if needed

## Disclaimer
- Informational analytics only; not investment advice, trade execution, or automated portfolio management
- Fallback figures are model inputs for grant prototyping and should be replaced with live verified data before production use

## Local run
```bash
cd backend && python3.11 -m pip install -e .[dev] && PYTHONPATH=src python3.11 -m uvicorn defi_pulse.api:app --reload
cd ../frontend && npm install && npm run dev
```

## Verification
```bash
cd backend && PYTHONPATH=src python3.11 -m pytest && python3.11 -m ruff check .
cd ../frontend && npm run build
```

## Notes
- Current data mode is `curated-fallback`, intentionally deterministic until live connectors are added.
- Next recommended step: replace curated inputs with live venue fetchers + persisted historical snapshots.

## Live connector stage
- `DEFI_PULSE_ENABLE_LIVE=1` enables a live Binance premium-index snapshot for the CEX carry leg.
- Base yield legs remain curated fallback until protocol-specific live adapters are added.
