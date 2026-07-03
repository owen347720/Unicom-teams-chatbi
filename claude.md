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

## Benchmark / 评测

- 当前主基准: `benchmark/v1.2-schema-gold-1000`
- Schema 来源: `benchmark/schema-live`，来自 A100 ClickHouse 实际表结构和样本画像
- 规模: `1000` 题，其中 `850` 条 gold SQL、`150` 条歧义/安全人工评审题
- Gold SQL 状态: `850/850` 已在 A100 执行成功，`0` 个 gold 错误
- 延迟快照: 平均 `1.402s`，P50 `0.295s`，P95 `5.975s`，最大 `8.828s`

评测说明见 `doc/EVAL.md`；持续优化记录见 `doc/CONTINUOUS_OPTIMIZATION.md`。`benchmark/v1.1-gold-1000` 已废弃为格式原型，不再作为主基准。
