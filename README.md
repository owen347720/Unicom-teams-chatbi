# Text2Sql - 团队内取数系统

基于 Vanna 的 Text2SQL 问数系统，支持自然语言转 SQL 查询。

## 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 MINIMAX_API_KEY

# 2. 一键启动
docker-compose up -d

# 3. 访问界面
浏览器打开: http://localhost:3000
```

## 交付部署

项目支持打包为离线镜像包，提供给其他组在 A100 服务器上部署：

```bash
IMAGE_TAG=2026-07-02 TARGET_PLATFORM=linux/amd64 ./scripts/build_release.sh
```

目标服务器加载镜像后执行：

```bash
docker compose -f docker-compose.release.yml --env-file .env up -d
```

详细步骤见 `doc/DEPLOY_A100.md`。

## 详细文档

见 `doc/` 目录。

## 更新日期

2026-07-02
