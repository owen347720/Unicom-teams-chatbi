"""
Vanna 集成核心 - VannaService 类
提供 SQL 生成和训练数据管理
"""

from openai import OpenAI
from vanna.base import VannaBase
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from typing import Dict, List
from loguru import logger
import os


class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna + ChromaDB + MiniMax-M2.7 集成服务
    提供 SQL 生成和训练数据管理
    """

    def __init__(self):
        """
        初始化 Vanna Service
        配置 MiniMax endpoint 和 ChromaDB
        """
        api_base = os.getenv(
            "MINIMAX_ENDPOINT", "http://10.242.52.62:9924"
        ) + "/v1"
        api_key = os.getenv("MINIMAX_API_KEY", "")
        model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
        chromadb_path = os.getenv("CHROMADB_PATH", "/data/chromadb")

        # 创建 OpenAI 兼容客户端（指向 MiniMax）
        client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )

        # ChromaDB 配置（不含 api_base）
        vector_config = {
            "path": chromadb_path,
        }

        # OpenAI Chat 配置（不含 api_base，使用 client）
        chat_config = {
            "api_key": api_key,
            "model": model,
        }

        ChromaDB_VectorStore.__init__(self, config=vector_config)
        OpenAI_Chat.__init__(self, client=client, config=chat_config)

        self.model = model
        logger.info(f"VannaService initialized with model: {self.model}")

    def train_ddl(self, datasource_name: str, ddl: str):
        """
        训练 DDL 信息

        Args:
            datasource_name: 数据源名称
            ddl: 表的 DDL 定义
        """
        try:
            # 使用 metadata 标记数据源
            self.train(ddl=ddl, metadata={"datasource": datasource_name})
            logger.info(f"DDL trained for {datasource_name}: {ddl[:50]}...")
        except Exception as e:
            logger.error(f"DDL training failed: {e}")
            raise

    def train_sql(
        self,
        datasource_name: str,
        question: str,
        sql: str,
    ):
        """
        训练问题-SQL对

        Args:
            datasource_name: 数据源名称
            question: 自然语言问题
            sql: SQL 查询语句
        """
        try:
            self.train(
                question=question,
                sql=sql,
                metadata={"datasource": datasource_name},
            )
            logger.info(f"SQL trained: {question}")
        except Exception as e:
            logger.error(f"SQL training failed: {e}")
            raise

    def generate_sql(
        self,
        datasource_name: str,
        question: str,
    ) -> Dict:
        """
        根据问题生成 SQL

        Args:
            datasource_name: 数据源名称
            question: 自然语言问题

        Returns:
            {
                'sql': 生成的SQL,
                'confidence': 置信度,
                'similar_questions': 相似问题列表
            }
        """
        try:
            # 使用 Vanna 的 generate_sql 方法生成 SQL
            sql = VannaBase.generate_sql(
                self,
                question=question,
                metadata={"datasource": datasource_name},
            )

            # 获取相似问题
            similar = self.get_similar_question_sql(question, n=5)

            logger.info(f"SQL generated for {datasource_name}: {sql[:100]}...")

            return {
                "sql": sql,
                "confidence": 0.8,  # Vanna 不提供置信度，默认返回
                "similar_questions": similar,
            }
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise

    def get_similar_training_data(
        self,
        question: str,
        n: int = 5,
    ) -> List[Dict]:
        """
        获取相似训练数据

        Args:
            question: 问题
            n: 返回数量

        Returns:
            [{question, sql, similarity}]
        """
        try:
            similar = self.get_similar_question_sql(question, n=n)
            return similar
        except Exception as e:
            logger.error(f"Similar data retrieval failed: {e}")
            return []
