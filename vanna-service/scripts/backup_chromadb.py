"""
ChromaDB 数据备份脚本
将 ChromaDB 中的训练数据导出为 JSON 格式
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger


def backup_chromadb(
    chromadb_path: str = None,
    output_dir: str = None,
    backup_filename: str = None,
) -> str:
    """
    备份 ChromaDB 数据到 JSON 文件

    Args:
        chromadb_path: ChromaDB 数据目录路径，默认从环境变量 CHROMADB_PATH 获取
        output_dir: 备份文件输出目录，默认为当前目录
        backup_filename: 备份文件名，默认自动生成带时间戳的文件名

    Returns:
        备份文件的完整路径
    """
    # 获取 ChromaDB 路径
    chromadb_path = chromadb_path or os.getenv("CHROMADB_PATH", "/data/chromadb")

    # 获取输出目录
    output_dir = output_dir or os.getenv("BACKUP_DIR", ".")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 生成备份文件名
    if backup_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"chromadb_backup_{timestamp}.json"

    backup_path = Path(output_dir) / backup_filename

    logger.info(f"Starting ChromaDB backup from {chromadb_path}")
    logger.info(f"Backup will be saved to {backup_path}")

    try:
        # 初始化 ChromaDB 客户端（只读模式）
        client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,
            ),
        )

        # 获取所有集合
        collection_names = client.list_collections()
        logger.info(f"Found {len(collection_names)} collections")

        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "chromadb_path": chromadb_path,
            "collections": [],
        }

        for collection in collection_names:
            # ChromaDB list_collections() 返回 Collection 对象
            collection_name = collection.name if hasattr(collection, 'name') else str(collection)
            logger.info(f"Backing up collection: {collection_name}")

            collection = client.get_collection(collection_name)

            # 获取集合中的所有数据
            result = collection.get(include=["embeddings", "documents", "metadatas"])

            collection_data = {
                "name": collection_name,
                "count": len(result["ids"]),
                "data": {
                    "ids": result["ids"],
                    "embeddings": result.get("embeddings", []),
                    "documents": result.get("documents", []),
                    "metadatas": result.get("metadatas", []),
                },
            }
            backup_data["collections"].append(collection_data)
            logger.info(f"  - Backed up {collection_data['count']} items")

        # 保存到 JSON 文件
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        total_items = sum(c["count"] for c in backup_data["collections"])
        logger.success(
            f"Backup completed: {backup_path} ({len(collection_names)} collections, "
            f"{total_items} items)"
        )

        return str(backup_path)

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Backup ChromaDB data to JSON file"
    )
    parser.add_argument(
        "--chromadb-path",
        type=str,
        default=None,
        help="ChromaDB data directory path (default: env CHROMADB_PATH or /data/chromadb)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for backup file (default: env BACKUP_DIR or current dir)",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="Backup filename (default: auto-generated with timestamp)",
    )

    args = parser.parse_args()

    try:
        backup_path = backup_chromadb(
            chromadb_path=args.chromadb_path,
            output_dir=args.output_dir,
            backup_filename=args.filename,
        )
        print(f"Backup created: {backup_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
