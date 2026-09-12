# NexusForge Frontend Deployment — Crash / Proxy / Sourcemap

Session: 2026-09-07 (Phase 6 final). Captures the recurring deploy/debug pattern for this React Vite SPA.

## Pattern
React SPA + FastAPI backend in Docker Compose. Blank white screen = fatal JS crash on mount (React fiber mount `Cg -> ne`). Must surface error (crash-catcher), trace via sourcemap, fix import/export mismatch or router context error, rebuild with sourcemap, verify via nginx proxy.

## Pitfall (encountered this session)
`useNavigate()` / `useLocation()` called at `App()` root (before `<Router>` wrapper at line 40) → React Router's `ne()` throws `"expected a router context"`. Source map points to `router.js:ne`; actual cause is hook placement.

## Fix sequence (validated)
1. Crash-catcher in `index.html`: `window.onerror` prints `error.name + error.message + error.stack`; Safari/iOS `msg` generic → `message` has real string.
2. Verify build: `vite.config.ts` `build: { sourcemap: true, assetsInlineLimit: 0 }`; bundle `.js.map` present.
3. Audit `App.tsx` imports — default vs named (`ProjectList` default, not `{ProjectList}`). Check `Activity.tsx` named imports on default-export files.
4. Remove root-level router hooks if they sit above `<Router>`; move `<BrowserRouter>` to `main.tsx` if needed.
5. Fix API base URL to relative (`/api`) + nginx `/api/` proxy with trailing slash (`proxy_pass http://backend:8000/`).
6. Add `location /ws/` upgrade block for WebSocket.
7. Rebuild: `docker-compose build frontend`; deploy: `up -d --build frontend backend`.

## Verification (must pass)
- `curl -s http://localhost:3000/` → HTML with crash-catcher + `#root`
- `curl -s http://localhost:3000/api/` → `{"name":"NexusForge API"}` (proxy works)
- `docker-compose ps` → frontend/backend/worker `Up`
- Source map `.js.map` exists in `/usr/share/nginx/html/assets/`

## Design-system tie
The design tokens (`#7C3AED` / `#0891B2`) and dark-mode crash-catcher styling (`#0f172a` bg / `#f87171` text) are the delivered UI's error-state presentation — this reference connects UI delivery to the deployment/debug loop.