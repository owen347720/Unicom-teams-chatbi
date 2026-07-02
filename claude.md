## 项目目标
本项目用于构建一个团队内取数项目，要求所有服务均在容器里发布，可直接插拔数据源后完成问数取数

## A100BMS-2 远程部署

- SSH: `A100BMS-2`
- 服务器目录: `/data1/text2sql/releases/amd64-verify`
- 前端: `http://192.168.3.9`
- 后端 API: `http://192.168.3.9:38000`
- Vanna: `http://192.168.3.9:38001`
- PostgreSQL 端口: `35432`

常用入口:

```bash
ssh A100BMS-2
cd /data1/text2sql/releases/amd64-verify
docker compose --env-file .env -f docker-compose.yml ps
```

运维详情见 `doc/A100_REMOTE_OPS.md`。服务器 `.env` 已配置生产模型和 ClickHouse 数据源凭据；不要把真实 key 或密码写入 git。

当前 Vanna 链路要求镜像内置 Chroma 默认 ONNX embedding 模型。`vanna-service/Dockerfile` 会在构建阶段下载并校验 `all-MiniLM-L6-v2`，因此 A100 运行时不依赖 `chroma-onnx-models.s3.amazonaws.com`。
