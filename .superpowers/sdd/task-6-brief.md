# Task 6: 实现 DDL 提取器

## 任务描述

实现 DDLExtractor 类，从不同数据库（ClickHouse、PostgreSQL、MySQL）提取表结构DDL信息。

## 文件清单

需要创建的文件：
- `vanna-service/app/ddl_extractor.py`
- `vanna-service/tests/test_ddl_extractor.py`

## 接口定义

- `DDLExtractor(db_type, connection_config)` - 初始化
- `extract_all_ddl() -> List[Dict]` - 提取所有表的DDL

## 实现要求

支持三种数据库：
- ClickHouse: `SHOW CREATE TABLE`
- PostgreSQL: `pg_get_tabledef()` 或信息schema
- MySQL: `SHOW CREATE TABLE`

完成后 Commit。报告写到 task-6-report.md。