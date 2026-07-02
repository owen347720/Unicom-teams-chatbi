# Frontend And Release Delivery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Complete the React frontend and add a release package path so another team can deploy the system on an A100 server with Docker Compose.

**Architecture:** Keep the existing microservice split: frontend, backend-api, vanna-service, and postgres. The frontend is a Vite React app served by nginx in production. Release delivery uses tagged Docker images, a release compose file, and scripts/docs for saving, loading, and starting the full stack on another server.

**Tech Stack:** React 18, TypeScript, Vite, Ant Design 5, Axios, TanStack Query, Monaco Editor, nginx, Docker Compose.

---

## New Delivery Constraint

The final project must be handoff-ready for another group to deploy on their A100 server. The target server should only need Docker and Docker Compose for normal startup. The release flow must support an offline or semi-offline transfer:

1. Build all service images.
2. Save images into a tar archive or release directory.
3. Copy the package to the A100 server.
4. Load images.
5. Configure `.env`.
6. Run `docker compose -f docker-compose.release.yml up -d`.

The MiniMax endpoint remains configurable by environment variable. The default remains `http://10.242.52.62:9924`.

## Task 16: React Project Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`

**Steps:**
1. Add package metadata and scripts: `dev`, `build`, `preview`, `lint`, `test`.
2. Add Vite React entry files.
3. Add a minimal smoke test for the initial app shell.
4. Run `npm install` if dependencies are not present.
5. Run `npm run build`.
6. Commit with `feat: scaffold frontend application`.

## Task 17: Frontend API Client And Types

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/services/api.test.ts`

**Steps:**
1. Write tests for URL construction and response normalization.
2. Implement typed Axios client with `VITE_API_BASE_URL`, defaulting to `/api`.
3. Add API functions for datasources, SQL generation/execution, history, training, and settings.
4. Run targeted frontend tests.
5. Commit with `feat: add frontend API client`.

## Task 18: Application Shell And Routing

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/pages/AskPage.tsx`
- Create: `frontend/src/pages/DataSourcesPage.tsx`
- Create: `frontend/src/pages/TrainingPage.tsx`
- Create: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/styles.css`

**Steps:**
1. Write component tests for shell rendering and section navigation.
2. Implement an Ant Design layout with top navigation.
3. Add pages for Ask, Data Sources, Training, and Settings.
4. Use a restrained operational-tool visual style: dense, readable, low decoration.
5. Run tests and build.
6. Commit with `feat: add frontend application shell`.

## Task 19: Ask Interface

**Files:**
- Modify: `frontend/src/pages/AskPage.tsx`
- Create: `frontend/src/components/SqlEditor.tsx`
- Create: `frontend/src/components/ResultTable.tsx`
- Test: `frontend/src/pages/AskPage.test.tsx`

**Steps:**
1. Write tests for generate SQL, edit SQL, execute SQL, and empty datasource states.
2. Implement datasource selection and natural language question input.
3. Add SQL preview/editor with Monaco, falling back gracefully in tests.
4. Add execution result table with row count and execution time.
5. Add query history panel.
6. Run tests and build.
7. Commit with `feat: implement ask interface`.

## Task 20: Data Source Manager

**Files:**
- Modify: `frontend/src/pages/DataSourcesPage.tsx`
- Test: `frontend/src/pages/DataSourcesPage.test.tsx`

**Steps:**
1. Write tests for list, add modal, connection test, delete confirmation.
2. Implement datasource list and add/edit form.
3. Support ClickHouse, PostgreSQL, and MySQL fields.
4. Hide stored passwords and only submit password values entered by the user.
5. Run tests and build.
6. Commit with `feat: implement datasource manager`.

## Task 21: Training Data Manager

**Files:**
- Modify: `frontend/src/pages/TrainingPage.tsx`
- Test: `frontend/src/pages/TrainingPage.test.tsx`

**Steps:**
1. Write tests for manual add, pending approvals, approve, delete.
2. Implement training table with filters for datasource/source/status.
3. Implement manual add/edit modal with SQL textarea/editor.
4. Add pending auto-training approval view.
5. Run tests and build.
6. Commit with `feat: implement training data manager`.

## Task 22: Settings And Health View

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Test: `frontend/src/pages/SettingsPage.test.tsx`

**Steps:**
1. Write tests for loading config and saving editable settings.
2. Implement settings form for MiniMax endpoint/model, timeout, max rows, and auto-train toggle.
3. Add read-only deployment/runtime hints without exposing secrets.
4. Run tests and build.
5. Commit with `feat: implement settings page`.

## Task 23: Frontend Production Container

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Modify: `docker-compose.yml`

**Steps:**
1. Add nginx config that serves static assets and proxies `/api` to backend.
2. Add multi-stage Dockerfile: Node build stage, nginx runtime stage.
3. Update compose frontend env/build as needed.
4. Build the frontend image.
5. Commit with `feat: add frontend production container`.

## Task 24: Release Compose And Packaging Scripts

**Files:**
- Create: `docker-compose.release.yml`
- Create: `scripts/build_release.sh`
- Create: `scripts/load_release.sh`
- Create: `scripts/verify_release.sh`
- Modify: `.env.example`

**Steps:**
1. Write release compose using `image:` tags instead of `build:`.
2. Add build script that builds tagged images and saves them to `release/text2sql-images.tar`.
3. Add load script for the target A100 server.
4. Add verify script that checks Docker, Compose, env file, and service health endpoints.
5. Extend `.env.example` for release image tag, MiniMax endpoint/model/API key, PostgreSQL, SQL limits, and encryption key.
6. Run shell syntax checks.
7. Commit with `feat: add release packaging workflow`.

## Task 25: Deployment Documentation

**Files:**
- Create: `doc/DEPLOY_A100.md`
- Modify: `README.md`
- Modify: `.superpowers/sdd/progress.md`

**Steps:**
1. Document source build startup for developers.
2. Document release package build on the source machine.
3. Document transfer/load/start on the A100 server.
4. Document required ports, volumes, environment variables, backup/restore, and troubleshooting.
5. Update progress ledger through completed tasks.
6. Commit with `docs: add A100 release deployment guide`.

## Task 26: Full Verification

**Files:**
- No new source files expected.

**Steps:**
1. Run backend import or test suite where available.
2. Run vanna-service tests.
3. Run frontend tests and production build.
4. Run Docker Compose config validation.
5. Build release images if Docker is available.
6. Record any environment blockers clearly.
7. Commit any final fixes.
