# A100 Remote Operations

This note records the live A100BMS-2 deployment for remote development and operations.

## Server

- SSH host: `A100BMS-2`
- Server hostname: `bms-wczx02`
- Architecture: `x86_64` / `linux/amd64`
- Deployment root: `/data1/text2sql`
- Active release: `/data1/text2sql/releases/amd64-verify`

## Ports

- Frontend: `http://192.168.3.9:38080`
- Backend API: `http://192.168.3.9:38000`
- Vanna service: `http://192.168.3.9:38001`
- PostgreSQL host port: `35432`

These ports were selected to avoid existing services on `3000`, `8000`, `5432`, `9911`, `9912`, `18000`, `18001`, `30070`, and `9083`.

## Current Runtime

Run commands from the active release directory:

```bash
ssh A100BMS-2
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml ps
```

Expected containers:

- `text2sql-frontend`
- `text2sql-backend`
- `text2sql-vanna`
- `text2sql-postgres`

## Health Checks

```bash
curl -fsS http://127.0.0.1:38080/health
curl -fsS http://127.0.0.1:38000/health
curl -fsS http://127.0.0.1:38001/health
```

The backend `/health` response currently reports its own status plus downstream status placeholders.

## Common Operations

Start or update:

```bash
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml up -d
```

Stop:

```bash
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml down
```

Logs:

```bash
docker logs --tail 200 text2sql-frontend
docker logs --tail 200 text2sql-backend
docker logs --tail 200 text2sql-vanna
docker logs --tail 200 text2sql-postgres
```

Restart one service:

```bash
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml restart backend-api
docker compose --env-file .env -f docker-compose.yml restart vanna-service
```

Load a replacement image:

```bash
cd /data1/text2sql/releases/amd64-verify
docker load -i text2sql-vanna-amd64-verify-fixed.tar
docker compose --env-file .env -f docker-compose.yml up -d --force-recreate vanna-service backend-api frontend
```

## Environment

Runtime env file:

```bash
/data1/text2sql/releases/amd64-verify/.env
```

Important values:

```bash
IMAGE_TAG=amd64-verify
TARGET_PLATFORM=linux/amd64
FRONTEND_PORT=38080
BACKEND_PORT=38000
VANNA_PORT=38001
POSTGRES_PORT=35432
CORS_ORIGINS=http://192.168.3.9:38080,http://localhost:38080
```

Before real model calls, replace `MINIMAX_API_KEY=your_api_key_here` in `.env` with the production key and restart `vanna-service` plus `backend-api`.

Current model endpoint:

```bash
MINIMAX_ENDPOINT=http://100.65.5.66:9940
MINIMAX_MODEL=MiniMax-M2.7
```

The runtime `.env` contains the production API key. Do not copy it into git.

## Current ClickHouse Datasource

- Name: `chatbi-clickhouse`
- Type: `clickhouse`
- Host: `100.65.5.66`
- Port: `9023`
- Database: `chatbi`
- User: `chatbi_user`

Port `9023` is the ClickHouse HTTP API, not the native TCP protocol. The backend supports this port through ClickHouse HTTP requests.

Smoke test:

```bash
cd /data1/text2sql/releases/amd64-verify
curl -fsS http://127.0.0.1:38000/api/v1/datasources/list
```

## Deployment Notes

- Docker root on the server is `/data1/docker`.
- The active compose file uses `postgres:15-alpine` because that image already exists on the server and avoids external image pulls.
- The release build script now saves `postgres:15-alpine` into future offline image archives.
- The Vanna image requires `openai==1.58.1`; this is now pinned in `vanna-service/requirements.txt`.
- The frontend container healthcheck uses `127.0.0.1:3000/health`; `localhost` fails inside the Alpine container on this server.
- The server cannot resolve `chroma-onnx-models.s3.amazonaws.com`, so Vanna has a direct MiniMax fallback when Chroma embedding initialization fails. This keeps SQL generation available even without the Chroma ONNX embedding model.
