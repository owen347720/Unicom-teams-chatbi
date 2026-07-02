## 项目目标
本项目用于构建一个团队内取数项目，要求所有服务均在容器里发布，可直接插拔数据源后完成问数取数

## A100BMS-2 远程部署

- SSH: `A100BMS-2`
- 服务器目录: `/data1/text2sql/releases/amd64-verify`
- 前端: `http://192.168.3.9:38080`
- 后端 API: `http://192.168.3.9:38000`
- Vanna: `http://192.168.3.9:38001`
- PostgreSQL 端口: `35432`

常用入口:

```bash
ssh A100BMS-2
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml ps
```

运维详情见 `doc/A100_REMOTE_OPS.md`。真实模型调用前需要把服务器 `.env` 中的 `MINIMAX_API_KEY=your_api_key_here` 替换为生产 key，并重启 `vanna-service` 和 `backend-api`。
