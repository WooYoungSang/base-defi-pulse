from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import urlopen

from pydantic import BaseModel

LIVE_ENV = 'DEFI_PULSE_ENABLE_LIVE'
URL_ENV = 'DEFI_PULSE_BINANCE_PREMIUM_INDEX_URL'
TIMEOUT_ENV = 'DEFI_PULSE_CONNECTOR_TIMEOUT_SEC'
DEFAULT_BINANCE_URL = 'https://fapi.binance.com/fapi/v1/premiumIndex?symbol=ETHUSDT'


class ConnectorStatus(BaseModel):
    name: str
    mode: Literal['live', 'curated-fallback']
    enabled: bool
    status: Literal['ok', 'disabled', 'fallback', 'error']
    detail: str
    checked_at: datetime
    payload: dict[str, Any] | None = None


class ConnectorsResponse(BaseModel):
    project: str
    data_mode: Literal['hybrid-live-fallback', 'curated-fallback']
    connectors: list[ConnectorStatus]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def live_enabled() -> bool:
    return os.getenv(LIVE_ENV, '0').lower() in {'1', 'true', 'yes', 'on'}


def _timeout_seconds() -> float:
    raw = os.getenv(TIMEOUT_ENV, '3.0')
    try:
        return max(0.5, min(float(raw), 10.0))
    except ValueError:
        return 3.0


def _fetch_binance_snapshot() -> dict[str, Any]:
    with urlopen(os.getenv(URL_ENV, DEFAULT_BINANCE_URL), timeout=_timeout_seconds()) as response:
        payload = json.loads(response.read().decode('utf-8'))

    funding_bps_8h = round(float(payload['lastFundingRate']) * 10_000, 4)
    annualized_funding = round(funding_bps_8h * 10.95 / 100, 4)
    return {
        'venue': 'Binance',
        'instrument': payload.get('symbol', 'ETHUSDT'),
        'mark_price': round(float(payload['markPrice']), 4),
        'index_price': round(float(payload['indexPrice']), 4),
        'last_funding_rate': float(payload['lastFundingRate']),
        'funding_bps_8h': funding_bps_8h,
        'annualized_funding_apy': annualized_funding,
        'next_funding_time': payload.get('nextFundingTime'),
        'time': payload.get('time'),
    }


def build_connectors_response() -> ConnectorsResponse:
    connectors: list[ConnectorStatus] = []
    live_ok = False

    if live_enabled():
        try:
            snapshot = _fetch_binance_snapshot()
            connectors.append(
                ConnectorStatus(
                    name='binance-premium-index',
                    mode='live',
                    enabled=True,
                    status='ok',
                    detail='Live Binance premium index snapshot loaded successfully.',
                    checked_at=_utcnow(),
                    payload=snapshot,
                )
            )
            live_ok = True
        except (KeyError, ValueError, URLError, TimeoutError) as exc:
            connectors.append(
                ConnectorStatus(
                    name='binance-premium-index',
                    mode='live',
                    enabled=True,
                    status='error',
                    detail=f'Live Binance fetch failed; continuing with curated fallback ({exc}).',
                    checked_at=_utcnow(),
                )
            )
    else:
        connectors.append(
            ConnectorStatus(
                name='binance-premium-index',
                mode='live',
                enabled=False,
                status='disabled',
                detail='Enable DEFI_PULSE_ENABLE_LIVE=1 to fetch live Binance funding snapshots.',
                checked_at=_utcnow(),
            )
        )

    connectors.append(
        ConnectorStatus(
            name='base-yield-basket',
            mode='curated-fallback',
            enabled=False,
            status='fallback',
            detail='Base yield basket remains curated fallback until protocol-specific live adapters are added.',
            checked_at=_utcnow(),
            payload={'protocols': ['Morpho Blue', 'Moonwell', 'Aave v3', 'Aerodrome', 'Uniswap v3']},
        )
    )

    return ConnectorsResponse(
        project='Base DeFi Pulse',
        data_mode='hybrid-live-fallback' if live_ok else 'curated-fallback',
        connectors=connectors,
    )
