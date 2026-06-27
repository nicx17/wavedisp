# WaveDisp Dashboard

This is the Vite/React control dashboard for WaveDisp.

## Development

```bash
npm install
npm run dev
```

The dashboard uses relative `/api/...` requests. During standalone Vite development, run the backend separately and configure a proxy if needed.

## Production Build

```bash
npm run build
```

The FastAPI backend serves the build from `dashboard/dist` by default. Override that path with `WAVEDISP_DASHBOARD_DIST` in the backend `.env`.

## Checks

```bash
npm run lint
npm run build
```
