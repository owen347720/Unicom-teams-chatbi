# A100 Server Deployment Guide

This guide describes how to package Text2SQL on a build machine and deploy it on another team's A100 server with Docker Compose.

## Target Server Requirements

- Docker Engine
- Docker Compose plugin (`docker compose version`)
- Ports available by default: `3000`, `8000`, `8001`, `5432`
- Network access from the A100 server to the MiniMax endpoint, default `http://10.242.52.62:9924`

GPU drivers are not required by this stack unless the MiniMax-compatible model service is also moved onto the A100 server later.

## Build A Release Package

Run on the source/build machine:

```bash
cp .env.example .env
IMAGE_TAG=2026-07-02 ./scripts/build_release.sh
```

The script creates `release/` with:

- `text2sql-images-<tag>.tar`
- `docker-compose.release.yml`
- `.env.example`
- `load_release.sh`
- `verify_release.sh`
- `README.txt`

Copy the whole `release/` directory to the A100 server.

## Start On The A100 Server

Run on the target server:

```bash
cd release
cp .env.example .env
```

Edit `.env`:

```bash
IMAGE_TAG=2026-07-02
MINIMAX_API_KEY=<real_key>
MINIMAX_ENDPOINT=http://10.242.52.62:9924
MINIMAX_MODEL=MiniMax-M2.7
ENCRYPTION_KEY=<stable_random_secret>
```

Load images and start:

```bash
./load_release.sh text2sql-images-2026-07-02.tar
./verify_release.sh
docker compose -f docker-compose.release.yml --env-file .env up -d
```

Open:

- Frontend: `http://<server-ip>:3000`
- Backend health: `http://<server-ip>:8000/health`
- Vanna health: `http://<server-ip>:8001/health`

## Data Persistence

Docker volumes store state:

- `postgres-data`: metadata, data sources, query history, training metadata
- `chromadb-data`: Vanna vector store
- `backend-logs`: backend logs

Back up ChromaDB with the scripts in `vanna-service/scripts/` when operating from source. For release deployments, back up Docker volumes according to the server team's standard process.

## Common Checks

```bash
docker compose -f docker-compose.release.yml --env-file .env ps
docker logs text2sql-backend --tail 100
docker logs text2sql-vanna --tail 100
docker logs text2sql-frontend --tail 100
```

If SQL generation fails, verify:

- `MINIMAX_API_KEY` is set.
- The A100 server can reach `MINIMAX_ENDPOINT`.
- Data source hosts are reachable from the Docker network.
