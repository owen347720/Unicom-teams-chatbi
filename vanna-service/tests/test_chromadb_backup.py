"""
测试 ChromaDB 备份和恢复脚本
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.backup_chromadb import backup_chromadb
from scripts.restore_chromadb import restore_chromadb


class TestBackupChromaDB:
    """测试 ChromaDB 备份功能"""

    def test_backup_creates_json_file(self):
        """测试备份创建 JSON 文件"""
        with tempfile.TemporaryDirectory() as chroma_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                # 创建测试用的 ChromaDB 数据
                import chromadb
                from chromadb.config import Settings

                client = chromadb.PersistentClient(
                    path=chroma_dir,
                    settings=Settings(anonymized_telemetry=False),
                )

                # 创建测试集合
                collection = client.create_collection("test_collection")
                collection.add(
                    ids=["id1", "id2"],
                    documents=["doc1", "doc2"],
                    metadatas=[{"key": "val1"}, {"key": "val2"}],
                    embeddings=[[0.1, 0.2], [0.3, 0.4]],
                )

                # 执行备份
                backup_path = backup_chromadb(
                    chromadb_path=chroma_dir,
                    output_dir=output_dir,
                    backup_filename="test_backup.json",
                )

                # 验证文件存在
                assert Path(backup_path).exists()
                assert Path(backup_path).suffix == ".json"

                # 验证备份内容
                with open(backup_path, "r") as f:
                    data = json.load(f)

                assert "backup_timestamp" in data
                assert "chromadb_path" in data
                assert "collections" in data
                assert len(data["collections"]) == 1
                assert data["collections"][0]["name"] == "test_collection"
                assert data["collections"][0]["count"] == 2

    def test_backup_auto_generates_filename(self):
        """测试备份自动生成文件名"""
        with tempfile.TemporaryDirectory() as chroma_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                import chromadb
                from chromadb.config import Settings

                client = chromadb.PersistentClient(
                    path=chroma_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                client.create_collection("test")

                # 不指定文件名
                backup_path = backup_chromadb(
                    chromadb_path=chroma_dir,
                    output_dir=output_dir,
                )

                # 验证文件名包含时间戳
                assert "chromadb_backup_" in backup_path
                assert Path(backup_path).exists()


class TestRestoreChromaDB:
    """测试 ChromaDB 恢复功能"""

    def test_restore_from_json_file(self):
        """测试从 JSON 文件恢复数据"""
        with tempfile.TemporaryDirectory() as chroma_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                # 首先创建一个备份
                import chromadb
                from chromadb.config import Settings

                # 创建源数据
                source_client = chromadb.PersistentClient(
                    path=chroma_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                collection = source_client.create_collection("test_collection")
                collection.add(
                    ids=["id1", "id2"],
                    documents=["doc1", "doc2"],
                    metadatas=[{"key": "val1"}, {"key": "val2"}],
                    embeddings=[[0.1, 0.2], [0.3, 0.4]],
                )

                # 备份
                backup_path = backup_chromadb(
                    chromadb_path=chroma_dir,
                    output_dir=output_dir,
                    backup_filename="test_backup.json",
                )

                # 创建新的 ChromaDB 目录
                with tempfile.TemporaryDirectory() as restore_dir:
                    # 恢复
                    stats = restore_chromadb(
                        backup_file=backup_path,
                        chromadb_path=restore_dir,
                    )

                    # 验证恢复结果
                    assert stats["collections_restored"] == 1
                    assert stats["items_restored"] == 2

                    # 验证数据 - 使用与恢复脚本相同的设置
                    target_client = chromadb.PersistentClient(
                        path=restore_dir,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True,
                        ),
                    )
                    restored_collection = target_client.get_collection("test_collection")
                    result = restored_collection.get()

                    assert len(result["ids"]) == 2
                    assert "id1" in result["ids"]
                    assert "id2" in result["ids"]

    def test_restore_skips_existing_collection(self):
        """测试恢复时跳过已存在的集合"""
        with tempfile.TemporaryDirectory() as chroma_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                import chromadb
                from chromadb.config import Settings

                # 创建源数据并备份
                source_client = chromadb.PersistentClient(
                    path=chroma_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                collection = source_client.create_collection("test_collection")
                collection.add(
                    ids=["id1"],
                    documents=["doc1"],
                    metadatas=[{"key": "val1"}],
                    embeddings=[[0.1, 0.2]],
                )

                backup_path = backup_chromadb(
                    chromadb_path=chroma_dir,
                    output_dir=output_dir,
                    backup_filename="test_backup.json",
                )

                # 创建已存在相同集合的目标 - 使用与恢复脚本相同的设置
                with tempfile.TemporaryDirectory() as restore_dir:
                    target_client = chromadb.PersistentClient(
                        path=restore_dir,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True,
                        ),
                    )
                    target_client.create_collection("test_collection")

                    # 恢复（不覆盖）
                    stats = restore_chromadb(
                        backup_file=backup_path,
                        chromadb_path=restore_dir,
                        force=False,
                    )

                    # 验证跳过
                    assert stats["collections_skipped"] == 1
                    assert stats["collections_restored"] == 0

    def test_restore_with_force_overwrite(self):
        """测试使用 force 参数覆盖已存在的集合"""
        with tempfile.TemporaryDirectory() as chroma_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                import chromadb
                from chromadb.config import Settings

                # 创建源数据并备份
                source_client = chromadb.PersistentClient(
                    path=chroma_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                collection = source_client.create_collection("test_collection")
                collection.add(
                    ids=["id1"],
                    documents=["doc1"],
                    metadatas=[{"key": "val1"}],
                    embeddings=[[0.1, 0.2]],
                )

                backup_path = backup_chromadb(
                    chromadb_path=chroma_dir,
                    output_dir=output_dir,
                    backup_filename="test_backup.json",
                )

                # 创建已存在相同集合的目标 - 使用与恢复脚本相同的设置
                with tempfile.TemporaryDirectory() as restore_dir:
                    target_client = chromadb.PersistentClient(
                        path=restore_dir,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True,
                        ),
                    )
                    target_client.create_collection("test_collection")

                    # 恢复（覆盖）
                    stats = restore_chromadb(
                        backup_file=backup_path,
                        chromadb_path=restore_dir,
                        force=True,
                    )

                    # 验证覆盖
                    assert stats["collections_restored"] == 1
                    assert stats["collections_skipped"] == 0

    def test_restore_invalid_backup_file(self):
        """测试恢复无效的备份文件"""
        with tempfile.TemporaryDirectory() as restore_dir:
            # 创建无效的备份文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write("{invalid json}")
                invalid_file = f.name

            with pytest.raises(json.JSONDecodeError):
                restore_chromadb(
                    backup_file=invalid_file,
                    chromadb_path=restore_dir,
                )


class TestBackupRestoreRoundTrip:
    """测试备份恢复完整流程"""

    def test_backup_and_restore_roundtrip(self):
        """测试备份和恢复的完整流程"""
        with tempfile.TemporaryDirectory() as source_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                import chromadb
                from chromadb.config import Settings

                # 创建源数据
                source_client = chromadb.PersistentClient(
                    path=source_dir,
                    settings=Settings(anonymized_telemetry=False),
                )
                collection = source_client.create_collection("my_collection")
                collection.add(
                    ids=["id1", "id2", "id3"],
                    documents=["question 1", "question 2", "question 3"],
                    metadatas=[
                        {"datasource": "db1"},
                        {"datasource": "db1"},
                        {"datasource": "db2"},
                    ],
                    embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
                )

                # 备份
                backup_path = backup_chromadb(
                    chromadb_path=source_dir,
                    output_dir=output_dir,
                    backup_filename="roundtrip.json",
                )

                # 恢复到新位置
                with tempfile.TemporaryDirectory() as target_dir:
                    stats = restore_chromadb(
                        backup_file=backup_path,
                        chromadb_path=target_dir,
                    )

                    # 验证统计
                    assert stats["collections_restored"] == 1
                    assert stats["items_restored"] == 3

                    # 验证数据完整性 - 使用与恢复脚本相同的设置
                    target_client = chromadb.PersistentClient(
                        path=target_dir,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True,
                        ),
                    )
                    restored = target_client.get_collection("my_collection")
                    result = restored.get(include=["documents", "metadatas"])

                    assert len(result["ids"]) == 3
                    assert set(result["documents"]) == {
                        "question 1",
                        "question 2",
                        "question 3",
                    }
                    datasources = [m["datasource"] for m in result["metadatas"]]
                    assert datasources.count("db1") == 2
                    assert datasources.count("db2") == 1
