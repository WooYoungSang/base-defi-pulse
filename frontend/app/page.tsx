'use client'

import { useEffect, useMemo, useState } from 'react'

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Confidence = 'high' | 'medium' | 'low'
type Risk = 'low' | 'medium' | 'high'

type Snapshot = {
  mean_cex_carry_apy: number
  mean_base_net_apy: number
  divergence_apy: number
  divergence_score: number
  regime: string
  top_protocol: string
  top_adjusted_edge_apy: number
}

type TrendPoint = {
  day: string
  cex_carry_apy: number
  base_net_apy: number
  divergence_apy: number
}

type Opportunity = {
  protocol: string
  strategy: string
  risk: Risk
  liquidity_musd: number
  edge_apy: number
  adjusted_edge_apy: number
  projected_monthly_edge_usd: number
  confidence: Confidence
  action: string
  rationale: string
}

type CexRate = {
  venue: string
  instrument: string
  funding_bps_8h: number
  funding_apy: number
  basis_apy: number
  carry_apy: number
  note: string
}

type BaseRate = {
  protocol: string
  strategy: string
  supply_apy: number
  incentive_apy: number
  borrow_cost_apy: number
  net_apy: number
  liquidity_musd: number
  risk: Risk
  note: string
}

type SummaryResponse = {
  project: string
  data_mode: string
  updated_at: string
  snapshot: Snapshot
  trend: TrendPoint[]
  top_opportunity: Opportunity
  calculator_preview: {
    capital_usd: number
    hedge_ratio: number
    operational_buffer_bps: number
    deployable_capital_usd: number
    gross_monthly_edge_usd: number
    monthly_buffer_cost_usd: number
    net_monthly_edge_usd: number
    break_even_days: number | null
    selected_protocol: string
    cex_benchmark: string
  }
  assumptions: string[]
}

type RatesResponse = {
  benchmark: string
  cex: CexRate[]
  base: BaseRate[]
}

type OpportunitiesResponse = {
  benchmark: string
  opportunities: Opportunity[]
}

type DashboardData = {
  summary: SummaryResponse
  rates: RatesResponse
  opportunities: OpportunitiesResponse
}

const FALLBACK_DATA: DashboardData = {
  summary: {
    project: 'Base DeFi Pulse',
    data_mode: 'curated-fallback',
    updated_at: '2026-04-18T07:00:00Z',
    snapshot: {
      mean_cex_carry_apy: 7.57,
      mean_base_net_apy: 11.68,
      divergence_apy: 4.11,
      divergence_score: 83,
      regime: 'base-yield-dominant',
      top_protocol: 'Morpho Blue',
      top_adjusted_edge_apy: 4.73,
    },
    trend: [
      { day: '2026-04-12', cex_carry_apy: 6.67, base_net_apy: 1.48, divergence_apy: 3.21 },
      { day: '2026-04-13', cex_carry_apy: 6.47, base_net_apy: 1.28, divergence_apy: 3.81 },
      { day: '2026-04-14', cex_carry_apy: 6.57, base_net_apy: 0.88, divergence_apy: 4.23 },
      { day: '2026-04-15', cex_carry_apy: 6.87, base_net_apy: 0.68, divergence_apy: 4.81 },
      { day: '2026-04-16', cex_carry_apy: 6.97, base_net_apy: 0.18, divergence_apy: 4.71 },
      { day: '2026-04-17', cex_carry_apy: 7.17, base_net_apy: 0.08, divergence_apy: 4.43 },
      { day: '2026-04-18', cex_carry_apy: 7.07, base_net_apy: -0.02, divergence_apy: 4.61 },
    ],
    top_opportunity: {
      protocol: 'Morpho Blue',
      strategy: 'cbBTC collateral / USDC lending loop',
      risk: 'low',
      liquidity_musd: 410,
      edge_apy: 5.03,
      adjusted_edge_apy: 4.73,
      projected_monthly_edge_usd: 236.5,
      confidence: 'high',
      action: 'Rotate delta-neutral carry into Morpho Blue and monitor liquidity utilization.',
      rationale:
        'Morpho Blue delivers 12.60% net APY versus 7.57% mean off-chain carry, leaving a 5.03% gross edge before policy haircuts.',
    },
    calculator_preview: {
      capital_usd: 100000,
      hedge_ratio: 0.6,
      operational_buffer_bps: 25,
      deployable_capital_usd: 60000,
      gross_monthly_edge_usd: 236.5,
      monthly_buffer_cost_usd: 20.83,
      net_monthly_edge_usd: 215.67,
      break_even_days: 3,
      selected_protocol: 'Morpho Blue',
      cex_benchmark: 'Mean CEX carry (Binance, Bybit, OKX)',
    },
    assumptions: [
      'Uses curated fallback data until live exchange and Base protocol connectors are wired in.',
      'Funding APY annualizes the latest 8h funding snapshot without leverage or fee rebates.',
      'Base net APY equals supply yield plus incentives minus explicit borrow or hedging costs.',
      'Operational buffer models execution slippage, gas, custody, and treasury policy overhead.',
    ],
  },
  rates: {
    benchmark: 'Mean CEX carry (Binance, Bybit, OKX)',
    cex: [
      {
        venue: 'Binance',
        instrument: 'ETH-PERP',
        funding_bps_8h: 0.45,
        funding_apy: 4.93,
        basis_apy: 2.6,
        carry_apy: 7.53,
        note: 'Funding cooled after CPI week; carry now driven more by basis than perp imbalance.',
      },
      {
        venue: 'Bybit',
        instrument: 'ETH-PERP',
        funding_bps_8h: 0.62,
        funding_apy: 6.79,
        basis_apy: 3.1,
        carry_apy: 9.89,
        note: 'Higher retail leverage keeps basis elevated, but not enough to dominate Base lending yields.',
      },
      {
        venue: 'OKX',
        instrument: 'ETH-PERP',
        funding_bps_8h: 0.28,
        funding_apy: 3.07,
        basis_apy: 2.2,
        carry_apy: 5.27,
        note: 'Most conservative venue in the basket; useful as a lower-bound carry benchmark.',
      },
    ],
    base: [
      {
        protocol: 'Morpho Blue',
        strategy: 'cbBTC collateral / USDC lending loop',
        supply_apy: 11.2,
        incentive_apy: 1.6,
        borrow_cost_apy: 0.2,
        net_apy: 12.6,
        liquidity_musd: 410,
        risk: 'low',
        note: 'Deep liquidity and predictable incentives make this the cleanest institutional carry leg on Base.',
      },
      {
        protocol: 'Moonwell',
        strategy: 'USDC supply with WELL incentives',
        supply_apy: 8.7,
        incentive_apy: 1.3,
        borrow_cost_apy: 0.1,
        net_apy: 9.9,
        liquidity_musd: 265,
        risk: 'low',
        note: 'Lower headline APY, but stable utilization and good fit for treasury idle cash.',
      },
      {
        protocol: 'Aave v3',
        strategy: 'USDC supply with safety-first posture',
        supply_apy: 7.9,
        incentive_apy: 0.9,
        borrow_cost_apy: 0.1,
        net_apy: 8.7,
        liquidity_musd: 350,
        risk: 'low',
        note: 'Strongest risk-adjusted option when policy requires blue-chip venue selection.',
      },
      {
        protocol: 'Aerodrome',
        strategy: 'WETH/USDC concentrated LP',
        supply_apy: 14.5,
        incentive_apy: 4.8,
        borrow_cost_apy: 3.7,
        net_apy: 15.6,
        liquidity_musd: 140,
        risk: 'high',
        note: 'Highest raw yield in the basket, but LP inventory drift warrants a larger haircut.',
      },
      {
        protocol: 'Uniswap v3',
        strategy: 'cbBTC/WETH concentrated LP',
        supply_apy: 11.8,
        incentive_apy: 2.7,
        borrow_cost_apy: 2.9,
        net_apy: 11.6,
        liquidity_musd: 92,
        risk: 'medium',
        note: 'Good directional fit when you already hold beta and want fees to subsidize exposure.',
      },
    ],
  },
  opportunities: {
    benchmark: 'Mean CEX carry (Binance, Bybit, OKX)',
    opportunities: [
      {
        protocol: 'Morpho Blue',
        strategy: 'cbBTC collateral / USDC lending loop',
        risk: 'low',
        liquidity_musd: 410,
        edge_apy: 5.03,
        adjusted_edge_apy: 4.73,
        projected_monthly_edge_usd: 215.67,
        confidence: 'high',
        action: 'Rotate delta-neutral carry into Morpho Blue and monitor liquidity utilization.',
        rationale:
          'Morpho Blue delivers 12.60% net APY versus 7.57% mean off-chain carry, leaving a 5.03% gross edge before policy haircuts.',
      },
      {
        protocol: 'Aerodrome',
        strategy: 'WETH/USDC concentrated LP',
        risk: 'high',
        liquidity_musd: 140,
        edge_apy: 8.03,
        adjusted_edge_apy: 5.46,
        projected_monthly_edge_usd: 252.17,
        confidence: 'low',
        action: 'Rotate delta-neutral carry into Aerodrome and monitor liquidity utilization.',
        rationale:
          'Aerodrome delivers 15.60% net APY versus 7.57% mean off-chain carry, leaving a 8.03% gross edge before policy haircuts.',
      },
      {
        protocol: 'Uniswap v3',
        strategy: 'cbBTC/WETH concentrated LP',
        risk: 'medium',
        liquidity_musd: 92,
        edge_apy: 4.03,
        adjusted_edge_apy: 3.3,
        projected_monthly_edge_usd: 144.17,
        confidence: 'low',
        action: 'Rotate delta-neutral carry into Uniswap v3 and monitor liquidity utilization.',
        rationale:
          'Uniswap v3 delivers 11.60% net APY versus 7.57% mean off-chain carry, leaving a 4.03% gross edge before policy haircuts.',
      },
      {
        protocol: 'Moonwell',
        strategy: 'USDC supply with WELL incentives',
        risk: 'low',
        liquidity_musd: 265,
        edge_apy: 2.33,
        adjusted_edge_apy: 2.19,
        projected_monthly_edge_usd: 88.67,
        confidence: 'high',
        action: 'Rotate delta-neutral carry into Moonwell and monitor liquidity utilization.',
        rationale:
          'Moonwell delivers 9.90% net APY versus 7.57% mean off-chain carry, leaving a 2.33% gross edge before policy haircuts.',
      },
    ],
  },
}

const percent = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 })
const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const compactUsd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  notation: 'compact',
  maximumFractionDigits: 1,
})

const pct = (value: number) => `${value.toFixed(2)}%`
const riskTone: Record<Risk, string> = {
  low: 'success',
  medium: 'warning',
  high: 'danger',
}

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, { cache: 'no-store' })
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`)
  }
  return (await response.json()) as T
}

function calculateEdge(opportunity: Opportunity, capital: number, hedgeRatio: number, bufferBps: number) {
  const deployableCapital = capital * hedgeRatio
  const grossMonthlyEdge = deployableCapital * (opportunity.adjusted_edge_apy / 100) / 12
  const monthlyBufferCost = capital * (bufferBps / 10_000) / 12
  const netMonthlyEdge = grossMonthlyEdge - monthlyBufferCost
  const breakEvenDays = grossMonthlyEdge <= 0 ? null : Math.max(1, Math.round(monthlyBufferCost / (grossMonthlyEdge / 30)))

  return {
    deployableCapital,
    grossMonthlyEdge,
    monthlyBufferCost,
    netMonthlyEdge,
    breakEvenDays,
  }
}

export default function HomePage() {
  const [summary, setSummary] = useState<SummaryResponse>(FALLBACK_DATA.summary)
  const [rates, setRates] = useState<RatesResponse>(FALLBACK_DATA.rates)
  const [opportunities, setOpportunities] = useState<Opportunity[]>(FALLBACK_DATA.opportunities.opportunities)
  const [selectedProtocol, setSelectedProtocol] = useState<string>(FALLBACK_DATA.summary.top_opportunity.protocol)
  const [capital, setCapital] = useState<number>(100000)
  const [hedgeRatio, setHedgeRatio] = useState<number>(0.6)
  const [bufferBps, setBufferBps] = useState<number>(25)
  const [mode, setMode] = useState<'live' | 'bundled'>('bundled')

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const [summaryResponse, ratesResponse, opportunitiesResponse] = await Promise.all([
          readJson<SummaryResponse>('/api/summary'),
          readJson<RatesResponse>('/api/rates'),
          readJson<OpportunitiesResponse>('/api/opportunities'),
        ])

        if (!active) {
          return
        }

        setSummary(summaryResponse)
        setRates(ratesResponse)
        setOpportunities(opportunitiesResponse.opportunities)
        setSelectedProtocol(summaryResponse.top_opportunity.protocol)
        setCapital(summaryResponse.calculator_preview.capital_usd)
        setHedgeRatio(summaryResponse.calculator_preview.hedge_ratio)
        setBufferBps(summaryResponse.calculator_preview.operational_buffer_bps)
        setMode('live')
      } catch {
        if (active) {
          setMode('bundled')
        }
      }
    }

    void load()

    return () => {
      active = false
    }
  }, [])

  const selectedOpportunity = useMemo(() => {
    return opportunities.find((item) => item.protocol === selectedProtocol) ?? opportunities[0]
  }, [opportunities, selectedProtocol])

  const calculator = useMemo(() => {
    return calculateEdge(selectedOpportunity, capital, hedgeRatio, bufferBps)
  }, [bufferBps, capital, hedgeRatio, selectedOpportunity])

  return (
    <main className="page shell">
      <section className="hero panel">
        <div>
          <div className="hero-head">
            <span className="badge">R4 real build</span>
            <span className={`status-pill ${mode === 'live' ? 'success' : 'warning'}`}>
              {mode === 'live' ? 'Live backend connected' : 'Bundled fallback snapshot'}
            </span>
          </div>
          <h1>{summary.project}</h1>
          <p>
            Compare ETH perp carry across major CEX venues against Base-native yield baskets, then quantify how
            much incremental monthly edge remains after risk haircuts and treasury overhead.
          </p>
          <div className="hero-callout">
            <strong>Regime:</strong> {summary.snapshot.regime} · <strong>Divergence:</strong>{' '}
            {pct(summary.snapshot.divergence_apy)} · <strong>Top protocol:</strong> {summary.snapshot.top_protocol}
          </div>
        </div>
        <div className="hero-stats">
          <MetricCard label="Mean CEX carry" value={pct(summary.snapshot.mean_cex_carry_apy)} hint={rates.benchmark} />
          <MetricCard label="Mean Base net APY" value={pct(summary.snapshot.mean_base_net_apy)} hint="Net of borrow / hedge drag" />
          <MetricCard label="Divergence score" value={`${summary.snapshot.divergence_score}/100`} hint="Higher means Base yields dominate" />
          <MetricCard label="Top adjusted edge" value={pct(summary.snapshot.top_adjusted_edge_apy)} hint={summary.top_opportunity.protocol} />
        </div>
      </section>

      <section className="grid two-up">
        <section className="panel">
          <div className="section-head">
            <h2>CEX carry basket</h2>
            <span>{rates.cex.length} venues</span>
          </div>
          <div className="stack-list">
            {rates.cex.map((entry) => (
              <article className="rate-card" key={entry.venue}>
                <div className="rate-header">
                  <div>
                    <h3>{entry.venue}</h3>
                    <p>{entry.instrument}</p>
                  </div>
                  <strong>{pct(entry.carry_apy)}</strong>
                </div>
                <dl className="detail-grid">
                  <div>
                    <dt>Funding APY</dt>
                    <dd>{pct(entry.funding_apy)}</dd>
                  </div>
                  <div>
                    <dt>Basis APY</dt>
                    <dd>{pct(entry.basis_apy)}</dd>
                  </div>
                  <div>
                    <dt>8h funding</dt>
                    <dd>{entry.funding_bps_8h.toFixed(2)} bps</dd>
                  </div>
                </dl>
                <p className="muted">{entry.note}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-head">
            <h2>Base yield basket</h2>
            <span>{rates.base.length} protocols</span>
          </div>
          <div className="stack-list">
            {rates.base.map((entry) => (
              <article className="rate-card" key={`${entry.protocol}-${entry.strategy}`}>
                <div className="rate-header">
                  <div>
                    <h3>{entry.protocol}</h3>
                    <p>{entry.strategy}</p>
                  </div>
                  <span className={`risk-pill ${riskTone[entry.risk]}`}>{entry.risk} risk</span>
                </div>
                <div className="yield-row">
                  <span>Supply {pct(entry.supply_apy)}</span>
                  <span>Incentives {pct(entry.incentive_apy)}</span>
                  <span>Borrow drag {pct(entry.borrow_cost_apy)}</span>
                </div>
                <div className="bar-shell">
                  <div className="bar-fill" style={{ width: `${Math.min(entry.net_apy * 4, 100)}%` }} />
                </div>
                <div className="rate-footer">
                  <strong>{pct(entry.net_apy)} net APY</strong>
                  <span>{compactUsd.format(entry.liquidity_musd * 1_000_000)} liquidity</span>
                </div>
                <p className="muted">{entry.note}</p>
              </article>
            ))}
          </div>
        </section>
      </section>

      <section className="grid two-up">
        <section className="panel">
          <div className="section-head">
            <h2>Divergence trend</h2>
            <span>7-day pulse</span>
          </div>
          <div className="trend-grid">
            {summary.trend.map((point) => (
              <div className="trend-col" key={point.day}>
                <span className="trend-label">{point.day.slice(5)}</span>
                <div className="trend-bars">
                  <div className="trend-bar trend-bar-base" style={{ height: `${point.base_net_apy * 5}px` }} />
                  <div className="trend-bar trend-bar-cex" style={{ height: `${point.cex_carry_apy * 5}px` }} />
                </div>
                <strong>{pct(point.divergence_apy)}</strong>
              </div>
            ))}
          </div>
          <p className="muted">Green bars track Base net yield. Blue bars track mean CEX carry. The spread has stayed positive throughout the week.</p>
        </section>

        <section className="panel">
          <div className="section-head">
            <h2>Ranked opportunities</h2>
            <span>Risk-adjusted</span>
          </div>
          <div className="stack-list compact">
            {opportunities.map((opportunity) => (
              <button
                type="button"
                className={`opportunity-card ${selectedProtocol === opportunity.protocol ? 'active' : ''}`}
                key={opportunity.protocol}
                onClick={() => setSelectedProtocol(opportunity.protocol)}
              >
                <div className="rate-header">
                  <div>
                    <h3>{opportunity.protocol}</h3>
                    <p>{opportunity.strategy}</p>
                  </div>
                  <strong>{pct(opportunity.adjusted_edge_apy)}</strong>
                </div>
                <div className="yield-row">
                  <span>Gross edge {pct(opportunity.edge_apy)}</span>
                  <span>{compactUsd.format(opportunity.liquidity_musd * 1_000_000)} TVL</span>
                  <span className={`confidence-pill ${opportunity.confidence}`}>{opportunity.confidence} conviction</span>
                </div>
                <p className="muted">{opportunity.rationale}</p>
              </button>
            ))}
          </div>
        </section>
      </section>

      <section className="grid two-up">
        <section className="panel calculator-panel">
          <div className="section-head">
            <h2>Why Base calculator</h2>
            <span>{selectedOpportunity.protocol}</span>
          </div>
          <div className="control-group">
            <label>
              Capital base
              <input type="range" min="25000" max="500000" step="25000" value={capital} onChange={(event) => setCapital(Number(event.target.value))} />
              <strong>{usd.format(capital)}</strong>
            </label>
            <label>
              Hedge ratio
              <input type="range" min="0.2" max="1" step="0.05" value={hedgeRatio} onChange={(event) => setHedgeRatio(Number(event.target.value))} />
              <strong>{percent.format(hedgeRatio)}</strong>
            </label>
            <label>
              Operational buffer
              <input type="range" min="5" max="100" step="5" value={bufferBps} onChange={(event) => setBufferBps(Number(event.target.value))} />
              <strong>{bufferBps} bps</strong>
            </label>
          </div>
          <div className="hero-stats calc-stats">
            <MetricCard label="Deployable capital" value={usd.format(calculator.deployableCapital)} hint="Capital multiplied by hedge ratio" />
            <MetricCard label="Gross monthly edge" value={usd.format(calculator.grossMonthlyEdge)} hint="Risk-adjusted spread capture" />
            <MetricCard label="Buffer cost" value={usd.format(calculator.monthlyBufferCost)} hint="Gas, custody, and ops reserve" />
            <MetricCard label="Net monthly edge" value={usd.format(calculator.netMonthlyEdge)} hint={calculator.breakEvenDays ? `Break-even in ~${calculator.breakEvenDays} days` : 'No break-even'} />
          </div>
          <p className="muted">{selectedOpportunity.action}</p>
        </section>

        <section className="panel">
          <div className="section-head">
            <h2>Operating assumptions</h2>
            <span>Fallback-friendly</span>
          </div>
          <ul className="assumptions-list">
            {summary.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
          <div className="note-box">
            <strong>Next integration step</strong>
            <p>
              Replace curated inputs with live venue connectors, then persist rolling snapshots so the divergence panel
              can show intraday and weekly regime changes.
            </p>
          </div>
        </section>
      </section>
    </main>
  )
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{hint}</p>
    </article>
  )
}
