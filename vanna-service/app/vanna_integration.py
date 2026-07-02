"""
Vanna 集成核心 - VannaService 类
提供 SQL 生成和训练数据管理
"""

from openai import OpenAI
from vanna.base import VannaBase
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from typing import Dict, List, Optional
from loguru import logger
import os
import re


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
        self.openai_client = client

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
        schema_context: Optional[str] = None,
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
                schema_context=schema_context,
            )
            sql = self._normalize_clickhouse_sql(sql)

            # 获取相似问题
            similar = self.get_similar_question_sql(question, n=5)

            logger.info(f"SQL generated for {datasource_name}: {sql[:100]}...")

            return {
                "sql": sql,
                "confidence": 0.8,  # Vanna 不提供置信度，默认返回
                "similar_questions": similar,
            }
        except Exception as e:
            logger.warning(
                f"Vanna SQL generation failed, falling back to direct LLM: {e}"
            )
            sql = self._generate_sql_with_llm(question, schema_context)
            sql = self._normalize_clickhouse_sql(sql)
            return {
                "sql": sql,
                "confidence": 0.3,
                "similar_questions": [],
            }

    def get_sql_prompt(
        self,
        initial_prompt: str,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        schema_context = kwargs.pop("schema_context", None)
        if schema_context:
            doc_list = [
                (
                    "实时数据库表结构和业务口径如下。必须只使用这些真实表和真实字段；"
                    "不要编造表名或字段名。明细类问题默认添加 LIMIT 100。"
                    "如果使用 UNION ALL，每个 SELECT 的列数、顺序和兼容类型必须一致，"
                    "并且只在整个 UNION ALL 结果末尾使用一个 LIMIT，或把每个分支包成子查询。\n"
                    f"{schema_context}"
                ),
                *doc_list,
            ]

        if initial_prompt is None:
            initial_prompt = (
                "You are a ClickHouse SQL expert. Generate executable SQL only. "
                "Do not explain. Do not use markdown fences. "
            )

        return super().get_sql_prompt(
            initial_prompt=initial_prompt,
            question=question,
            question_sql_list=question_sql_list,
            ddl_list=ddl_list,
            doc_list=doc_list,
            **kwargs,
        )

    def _generate_sql_with_llm(
        self, question: str, schema_context: Optional[str] = None
    ) -> str:
        context = schema_context or "未提供表结构。"
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 ClickHouse SQL 生成器。必须只使用用户提供的真实表和真实字段。"
                        "如果表结构不足以回答，也不要编造表名或字段名；优先返回一条可执行的探索性 SQL。"
                        "如果使用 UNION ALL，每个 SELECT 的列数、顺序和兼容类型必须一致，"
                        "并且只在整个 UNION ALL 结果末尾使用一个 LIMIT。"
                        "只输出可执行 SQL，不要解释，不要 markdown 代码块。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"表结构和业务口径:\n{context}\n\n"
                        f"用户问题:\n{question}"
                    ),
                },
            ],
            max_tokens=512,
        )
        content = response.choices[0].message.content or ""
        return self._strip_sql_markdown(content)

    def _strip_sql_markdown(self, value: str) -> str:
        value = value.strip()
        match = re.search(
            r"```(?:sql)?\s*(.*?)```", value, flags=re.IGNORECASE | re.DOTALL
        )
        if match:
            value = match.group(1).strip()
        return value.rstrip(";") + ";"

    def _normalize_clickhouse_sql(self, value: str) -> str:
        sql = self._strip_sql_markdown(value)
        if not re.search(r"\bUNION\s+ALL\b", sql, flags=re.IGNORECASE):
            return sql

        limits = [
            int(match.group(1))
            for match in re.finditer(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
        ]
        if len(limits) <= 1:
            return sql

        sql_without_limits = re.sub(
            r"\s+\bLIMIT\s+\d+\b\s*;?",
            " ",
            sql,
            flags=re.IGNORECASE,
        ).strip()
        limit = min(limits)
        return f"{sql_without_limits.rstrip(';')}\nLIMIT {limit};"

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
