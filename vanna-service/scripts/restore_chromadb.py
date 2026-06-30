"""
ChromaDB 数据恢复脚本
从 JSON 备份文件恢复 ChromaDB 数据
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger


def restore_chromadb(
    backup_file: str,
    chromadb_path: str = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    从 JSON 备份文件恢复 ChromaDB 数据

    Args:
        backup_file: 备份文件的路径
        chromadb_path: ChromaDB 数据目录路径，默认从环境变量 CHROMADB_PATH 获取
        force: 如果为 True，覆盖已存在的集合数据；如果为 False，则跳过已存在的集合

    Returns:
        恢复结果统计信息，包含恢复的集合数和项目数
    """
    # 验证备份文件
    backup_path = Path(backup_file)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    # 获取 ChromaDB 路径
    chromadb_path = chromadb_path or os.getenv("CHROMADB_PATH", "/data/chromadb")

    logger.info(f"Starting ChromaDB restore from {backup_file}")
    logger.info(f"Target ChromaDB path: {chromadb_path}")

    try:
        # 加载备份数据
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        # 验证备份文件格式
        if "collections" not in backup_data:
            raise ValueError("Invalid backup file: missing 'collections' key")

        # 确保目标目录存在
        Path(chromadb_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB 客户端
        client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # 获取现有集合列表
        existing_collections = set()
        for coll in client.list_collections():
            coll_name = coll.name if hasattr(coll, 'name') else str(coll)
            existing_collections.add(coll_name)
        logger.info(f"Found {len(existing_collections)} existing collections")

        # 恢复统计
        stats = {
            "collections_restored": 0,
            "collections_skipped": 0,
            "items_restored": 0,
            "items_skipped": 0,
        }

        for collection_data in backup_data["collections"]:
            collection_name = collection_data["name"]
            collection_info = collection_data.get("data", {})

            # 检查集合是否已存在
            if collection_name in existing_collections and not force:
                logger.warning(
                    f"Collection '{collection_name}' already exists. "
                    "Use --force to overwrite."
                )
                stats["collections_skipped"] += 1
                stats["items_skipped"] += collection_data.get("count", 0)
                continue

            # 删除已存在的集合（如果 force=True）
            if collection_name in existing_collections and force:
                logger.info(f"Deleting existing collection: {collection_name}")
                client.delete_collection(collection_name)

            # 创建新集合
            logger.info(f"Creating collection: {collection_name}")
            coll_metadata = collection_data.get("metadata")
            # ChromaDB 要求 metadata 不能是空 dict，使用 None 代替
            if coll_metadata == {}:
                coll_metadata = None
            collection = client.create_collection(
                name=collection_name,
                metadata=coll_metadata,
            )

            # 获取数据
            ids = collection_info.get("ids", [])
            documents = collection_info.get("documents", [])
            metadatas = collection_info.get("metadatas", [])
            embeddings = collection_info.get("embeddings", [])

            if not ids:
                logger.warning(f"Collection '{collection_name}' has no data to restore")
                stats["collections_restored"] += 1
                continue

            # 分批添加数据（避免一次性加载大量数据）
            batch_size = 100
            total_items = len(ids)

            for i in range(0, total_items, batch_size):
                batch_end = min(i + batch_size, total_items)
                batch_ids = ids[i:batch_end]
                batch_docs = documents[i:batch_end] if documents else None
                batch_meta = metadatas[i:batch_end] if metadatas else None
                batch_embed = embeddings[i:batch_end] if embeddings else None

                collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_meta,
                    embeddings=batch_embed,
                )
                logger.info(
                    f"  - Restored {batch_end}/{total_items} items "
                    f"for collection '{collection_name}'"
                )

            stats["collections_restored"] += 1
            stats["items_restored"] += total_items
            logger.success(
                f"Collection '{collection_name}' restored "
                f"({total_items} items)"
            )

        logger.success(
            f"Restore completed: {stats['collections_restored']} collections restored, "
            f"{stats['items_restored']} items restored"
        )
        if stats["collections_skipped"] > 0:
            logger.warning(
                f"Skipped: {stats['collections_skipped']} collections, "
                f"{stats['items_skipped']} items"
            )

        return stats

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in backup file: {e}")
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Restore ChromaDB data from JSON backup file"
    )
    parser.add_argument(
        "backup_file",
        type=str,
        help="Path to the backup JSON file",
    )
    parser.add_argument(
        "--chromadb-path",
        type=str,
        default=None,
        help="ChromaDB data directory path (default: env CHROMADB_PATH or /data/chromadb)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing collections if they exist",
    )

    args = parser.parse_args()

    try:
        stats = restore_chromadb(
            backup_file=args.backup_file,
            chromadb_path=args.chromadb_path,
            force=args.force,
        )
        print(f"Restore completed successfully:")
        print(f"  - Collections restored: {stats['collections_restored']}")
        print(f"  - Items restored: {stats['items_restored']}")
        if stats['collections_skipped'] > 0:
            print(f"  - Collections skipped: {stats['collections_skipped']}")
            print(f"  - Items skipped: {stats['items_skipped']}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
