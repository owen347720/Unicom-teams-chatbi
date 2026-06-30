diff --git a/docker-compose.yml b/docker-compose.yml
new file mode 100644
index 0000000..1513b71
--- /dev/null
+++ b/docker-compose.yml
@@ -0,0 +1,91 @@
+version: '3.8'
+
+services:
+  # 前端服务
+  frontend:
+    build: ./frontend
+    container_name: text2sql-frontend
+    ports:
+      - "3000:3000"
+    environment:
+      - REACT_APP_API_URL=http://localhost:8000
+      - NODE_ENV=production
+    depends_on:
+      - backend-api
+    networks:
+      - text2sql-network
+    restart: always
+
+  # 后端 API 服务
+  backend-api:
+    build: ./backend
+    container_name: text2sql-backend
+    ports:
+      - "8000:8000"
+    environment:
+      - VANNA_SERVICE_URL=http://vanna-service:8001
+      - DATABASE_URL=postgresql://text2sql:text2sql123@postgres:5432/text2sql
+      - CORS_ORIGINS=http://localhost:3000
+      - SQL_TIMEOUT=60
+      - MAX_RESULT_ROWS=1000
+    volumes:
+      - ./backend/logs:/app/logs
+    depends_on:
+      - vanna-service
+      - postgres
+    networks:
+      - text2sql-network
+    restart: always
+    healthcheck:
+      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
+      interval: 30s
+      timeout: 10s
+      retries: 3
+
+  # Vanna AI 服务
+  vanna-service:
+    build: ./vanna-service
+    container_name: text2sql-vanna
+    ports:
+      - "8001:8001"
+    environment:
+      - MINIMAX_ENDPOINT=http://10.242.52.62:9924
+      - MINIMAX_MODEL=MiniMax-M2.7
+      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
+      - CHROMADB_PATH=/data/chromadb
+    volumes:
+      - chromadb-data:/data/chromadb
+    networks:
+      - text2sql-network
+    restart: always
+    healthcheck:
+      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
+      interval: 30s
+      timeout: 10s
+      retries: 3
+
+  # PostgreSQL 元数据存储
+  postgres:
+    image: postgres:15
+    container_name: text2sql-postgres
+    ports:
+      - "5432:5432"
+    environment:
+      - POSTGRES_USER=text2sql
+      - POSTGRES_PASSWORD=text2sql123
+      - POSTGRES_DB=text2sql
+    volumes:
+      - postgres-data:/var/lib/postgresql/data
+    networks:
+      - text2sql-network
+    restart: always
+
+volumes:
+  chromadb-data:
+    driver: local
+  postgres-data:
+    driver: local
+
+networks:
+  text2sql-network:
+    driver: bridge
