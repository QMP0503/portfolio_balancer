# Phase 6 — React Frontend

## Goal
Deploy-ready UI for payday use. One screen that shows allocation, what to buy, and when to buy it.
Deploy fast — Phase 8 (server) is the real target. This phase gets the frontend to a usable state.

---

## Stack
| Tool | Why |
|------|-----|
| React + Vite | Fast dev server, you know it |
| Tailwind CSS | Utility-first, mobile-first by default |
| Recharts | Simple charting, React-native, no D3 overhead |
| React Router | Client-side routing between login / dashboard / settings |

**Dark mode strategy:** `darkMode: 'class'` in Tailwind config. ThemeContext persists choice to localStorage. Toggle in top bar. Dark is the default.

---

## Approved UI Decisions

### Contribution input
- Editable field on the dashboard (not a setting)
- User types amount → clicks "Calculate" → recommendations update
- Not persisted — entered fresh each payday

### Portfolio selector
- Dropdown at top of dashboard
- Lists all user portfolios
- Last option: "+ Add Portfolio" → opens `AddPortfolioModal`

### Add Portfolio — 3-step modal
```
Step 1: Account name
  ○ TFSA  ○ FHSA  ○ RRSP  ○ Non-registered  ○ Other [_____]

Step 2: Current holdings  (prices auto-fetched from GET /quotes/latest)
  HXQ.TO   [___] shares   @ $45.21  =  $0
  VFV.TO   [___] shares   @ $108.79 =  $0
  VCN.TO   [___] shares   @ $67.89  =  $0
  ZEM.TO   [___] shares   @ $40.02  =  $0

Step 3: Target allocations  (must sum to 100%)
  HXQ.TO   [35] %
  VFV.TO   [40] %
  VCN.TO   [15] %
  ZEM.TO   [10] %
  Total: 100% ✓   [Save]
```

### Holdings update
- Both locations: inline edit on Settings → Holdings tab AND inline edit from allocation view
- Input replaces total (not a delta — enter new total share count)

### Empty state
- If user has no portfolios, dashboard shows "Add your first portfolio" prompt (no wizard — wizard deferred to Phase 6.6)

---

## Dashboard layout (north star)
```
┌─────────────────────────────────────────────────┐
│  [Portfolio: TFSA ▾]           [☾]  [Settings]  │
├─────────────────────────────────────────────────┤
│  Total Value: $46,397 CAD      +25.1% all time  │
│                                                  │
│  Allocation                                      │
│  HXQ  ████████████  46.7% → 35%  ↓ overweight  │
│  VFV  █████████     32.6% → 40%  ↑ underweight  │
│  VCN  ████          12.1% → 15%  ↑ underweight  │
│  ZEM  █             4.3%  → 10%  ↑ underweight  │
│                                                  │
│  Contribute: [ $1,200 ]  [→ Calculate]           │
│                                                  │
│  Recommended buys:                               │
│  VFV  → 3 shares  @ $108.79  =  $326            │
│  VCN  → 4 shares  @ $67.89   =  $272            │
│  ZEM  → 15 shares @ $40.02   =  $600            │
│  HXQ  → skip (overweight)                       │
│  Leftover: $2.00                                 │
│                                                  │
│  Best time to buy today: 11:00 – 14:00 EST      │
│  ⚠ ZEM spread 2.1x wider than normal            │
└─────────────────────────────────────────────────┘
```

---

## Files — Build Order

### 1. Vite project scaffold
```
etf-intelligence/frontend/
```
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install recharts react-router-dom
```
Tailwind config: `darkMode: 'class'`
Vite config: proxy `/api` → `http://backend:8000` (avoids CORS in dev)

---

### 2. `src/api.js`
All API calls in one place. Cookies sent automatically (credentials: 'include').

Functions to implement:
```js
// Auth
login(email, password, rememberMe)
register(email, firstName, lastName, password)
logout()

// Portfolios
getPortfolios()
createPortfolio(accountName)
getAllocations(portfolioId)
setAllocation(portfolioId, ticker, targetPct, goal)

// Holdings
getHoldings(portfolioId)
updateHolding(portfolioId, ticker, shares)

// Quotes
getLatestQuotes()

// Rebalancer
getRecommendations(portfolioId, contributionCad)
getTiming()
```

---

### 3. `src/context/ThemeContext.jsx`
- Reads saved preference from localStorage on mount
- Applies/removes `dark` class on `<html>` element
- Exposes `{ theme, toggleTheme }` to all components

---

### 4. `src/App.jsx`
- Auth state: check for active session on load (GET /portfolios — 401 means logged out)
- Routes: `/login` → `<Login>`, `/` → `<Dashboard>`, `/settings` → `<Settings>`
- Redirect unauthenticated users to `/login`

---

### 5. `src/components/Login.jsx`
- Email + password fields
- Remember me checkbox
- Error message on 401
- Redirects to `/` on success

---

### 6. `src/components/Dashboard.jsx`
- Fetches: portfolios, allocations, holdings, quotes, timing on mount
- Owns `selectedPortfolioId` state
- Owns `contributionCad` state (number input)
- Triggers recommendation fetch when "Calculate" clicked
- Renders: portfolio selector, allocation chart, buy recommendations, timing, empty state

---

### 7. `src/components/Allocation.jsx`
Props: `{ holdings, allocations, quotes }`

- Computes current value per ETF (shares × price)
- Computes current % of total
- Recharts `BarChart` — two horizontal bars per ETF: current % (blue) vs target % (grey dashed)
- Overweight label (↓ red), underweight label (↑ green)

---

### 8. `src/components/BuyRecommendation.jsx`
Props: `{ recommendations, contributionCad, onContributionChange, onCalculate }`

- Contribution input + Calculate button at top
- Table: Ticker / Shares / Price / Total / Note
- Leftover cash shown at bottom
- Skipped tickers show "Skip — overweight" in Note column

---

### 9. `src/components/ExecutionTiming.jsx`
Props: `{ windows }`

- One row per ETF: ticker, best window (e.g. "11:00 – 14:00 EST")
- Spread warning badge if spread is anomalous (placeholder until Phase 7 data exists)

---

### 10. `src/components/AddPortfolioModal.jsx`
Props: `{ quotes, onClose, onCreated }`

State machine: `step` ∈ {1, 2, 3}

- Step 1: account name radio + Other free text
- Step 2: shares input per ETF, price auto-filled from quotes
- Step 3: target % per ETF, running total, Save button disabled until total = 100
- On Save: POST /portfolios → PUT allocations → PUT holdings → call onCreated

---

### 11. `src/components/Settings.jsx`
Two tabs: **Holdings** and **Allocations**

**Holdings tab:**
- Table: ticker / shares / last updated / [edit button]
- Click edit → inline input → save calls PUT /portfolios/{id}/holdings/{ticker}

**Allocations tab:**
- Table: ticker / target % / goal / [edit button]
- Click edit → inline inputs → save calls PUT /portfolios/{id}/allocations/{ticker}

---

### 12. `docker-compose.yml` update
Add frontend service:
```yaml
frontend:
  build: ./frontend
  ports:
    - "5173:5173"
  volumes:
    - ./frontend:/app
    - /app/node_modules
  command: npm run dev -- --host
  depends_on:
    - backend
```

---

## What's Deferred (not Phase 6)

| Item | Why deferred | When |
|------|-------------|------|
| `Performance.jsx` | No historical data yet | Phase 7 |
| `SpreadAnalysis.jsx` | Needs weeks of data | Phase 7 |
| First-login setup wizard | Build after deploy when missing UX is clear | Phase 6.6 |
| Registration UI | Only one user for now — register via API | Phase 6.6 |
| Multi-portfolio analytics | Need data first | Post-deploy |

---

## API endpoints this phase consumes

| Endpoint | Used by |
|----------|---------|
| POST /auth/login | Login.jsx |
| POST /auth/logout | App.jsx top bar |
| GET /portfolios | Dashboard.jsx, App.jsx |
| POST /portfolios | AddPortfolioModal.jsx |
| GET /portfolios/{id}/allocations | Dashboard.jsx, Settings.jsx |
| PUT /portfolios/{id}/allocations/{ticker} | AddPortfolioModal.jsx, Settings.jsx |
| GET /portfolios/{id}/holdings | Dashboard.jsx, Settings.jsx |
| PUT /portfolios/{id}/holdings/{ticker} | AddPortfolioModal.jsx, Settings.jsx |
| GET /quotes/latest | Dashboard.jsx, AddPortfolioModal.jsx |
| GET /rebalancer/{id}/recommend | BuyRecommendation.jsx (on Calculate) |
| GET /rebalancer/timing | ExecutionTiming.jsx |

---

## Verification (when done)
```bash
# All 36 backend tests still pass
docker compose exec backend python -m pytest tests/api/ -q

# Frontend dev server loads
open http://localhost:5173

# Can log in, see dashboard, run a calculation
```
