from fastapi.testclient import TestClient

from defi_pulse.api import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "defi_pulse"
    assert body["live_connectors_enabled"] is False


def test_summary_exposes_divergence_snapshot() -> None:
    response = client.get("/api/summary")
    assert response.status_code == 200

    body = response.json()
    assert body["project"] == "Base DeFi Pulse"
    assert body["data_mode"] == "curated-fallback"
    assert body["snapshot"]["regime"] == "base-yield-dominant"
    assert body["snapshot"]["divergence_apy"] > 0
    assert len(body["trend"]) == 7
    assert body["top_opportunity"]["protocol"] == body["snapshot"]["top_protocol"]


def test_rates_exposes_curated_cex_and_base_baskets() -> None:
    response = client.get("/api/rates")
    assert response.status_code == 200

    body = response.json()
    assert len(body["cex"]) == 3
    assert len(body["base"]) == 5
    assert body["averages"]["base_net_apy"] > body["averages"]["cex_carry_apy"]
    assert all(entry["carry_apy"] > 0 for entry in body["cex"])


def test_opportunities_are_ranked_by_adjusted_edge() -> None:
    response = client.get(
        "/api/opportunities",
        params={"capital": 120000, "hedge_ratio": 0.75, "operational_buffer_bps": 30},
    )
    assert response.status_code == 200

    opportunities = response.json()["opportunities"]
    assert len(opportunities) >= 3
    assert opportunities[0]["adjusted_edge_apy"] >= opportunities[1]["adjusted_edge_apy"]
    assert opportunities[0]["projected_monthly_edge_usd"] > opportunities[-1]["projected_monthly_edge_usd"]


def test_calculator_accepts_protocol_override() -> None:
    response = client.get(
        "/api/calculator",
        params={
            "capital": 150000,
            "hedge_ratio": 0.7,
            "operational_buffer_bps": 20,
            "protocol": "Moonwell",
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert body["selected_protocol"] == "Moonwell"
    assert body["deployable_capital_usd"] == 105000.0
    assert body["net_monthly_edge_usd"] > 0


def test_invalid_calculator_input_is_rejected() -> None:
    response = client.get("/api/calculator", params={"capital": 0})
    assert response.status_code == 422


def test_connectors_endpoint_defaults_to_fallback_or_disabled() -> None:
    response = client.get("/api/connectors")
    assert response.status_code == 200

    body = response.json()
    assert body["project"] == "Base DeFi Pulse"
    assert len(body["connectors"]) == 2
    assert body["connectors"][0]["status"] in {"disabled", "ok", "error"}
    assert body["connectors"][1]["status"] == "fallback"
