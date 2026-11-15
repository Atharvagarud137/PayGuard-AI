# PayGuard-AI dashboard

React 19 + TypeScript + Vite dashboard for the synthetic PayGuard-AI payment gateway.

The dashboard currently provides overview, card and transaction views. It is a local development/test interface, not a production operations console.

## Requirements

- Node.js 22 (the CI version)
- npm
- PayGuard-AI FastAPI backend at `http://localhost:8000`

## Run

From this directory:

```powershell
npm ci
npm run dev
```

Vite serves the dashboard at `http://localhost:5173`.

Create a production build:

```powershell
npm run build
```

Run the configured linter:

```powershell
npm run lint
```

## Backend connection and authentication limitation

The API client in `src/services/api.ts` currently hardcodes `http://localhost:8000/api/v1` and does not send `X-API-Key`. The backend allows keyless access only when `PAYGUARD_ENV=development` or `test` and no service key is configured. Production requires a service key, so this dashboard client is not production-compatible as currently written.

Do not place a production API key in a Vite `VITE_*` variable: values exposed to browser code are public to users. A production design needs a server-side proxy or another deliberate credential flow.

The dashboard uses synthetic payment data only. It is not connected to real card networks or payment processors.
