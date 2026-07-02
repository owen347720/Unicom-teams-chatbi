import { Alert, Button, Input, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { ResultTable } from '../components/ResultTable';
import { SqlEditor } from '../components/SqlEditor';
import { askApi, datasourceApi } from '../services/api';
import type { Datasource, ExecuteSqlResponse, QueryHistory } from '../types';

export function AskPage() {
  const [datasources, setDatasources] = useState<Datasource[]>([]);
  const [datasourceId, setDatasourceId] = useState('');
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<ExecuteSqlResponse | null>(null);
  const [history, setHistory] = useState<QueryHistory[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState<'generate' | 'execute' | ''>('');

  useEffect(() => {
    let mounted = true;

    async function loadInitialData() {
      try {
        const [datasourceResponse, historyResponse] = await Promise.all([
          datasourceApi.list(),
          askApi.history(),
        ]);
        if (!mounted) return;
        setDatasources(datasourceResponse.items);
        setDatasourceId(datasourceResponse.items[0]?.id ?? '');
        setHistory(historyResponse.items);
      } catch (err) {
        if (mounted) setError(err instanceof Error ? err.message : '加载问数数据失败');
      }
    }

    loadInitialData();
    return () => {
      mounted = false;
    };
  }, []);

  async function generateSql() {
    if (!datasourceId || !question.trim()) return;
    setError('');
    setLoading('generate');
    try {
      const response = await askApi.generateSql({
        datasource_id: datasourceId,
        question: question.trim(),
      });
      setSql(response.sql);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 SQL 失败');
    } finally {
      setLoading('');
    }
  }

  async function executeSql() {
    if (!datasourceId || !sql.trim()) return;
    setError('');
    setLoading('execute');
    try {
      const response = await askApi.executeSql({
        datasource_id: datasourceId,
        sql: sql.trim(),
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : '执行 SQL 失败');
    } finally {
      setLoading('');
    }
  }

  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>问数</Typography.Title>
          <Typography.Paragraph>选择数据源，输入自然语言问题，生成可审阅 SQL 后执行查询。</Typography.Paragraph>
        </div>
      </div>
      {error ? <Alert type="error" message={error} showIcon className="section-alert" /> : null}
      <div className="ask-grid">
        <Space direction="vertical" size={12} className="full-width">
          <label className="field-block">
            <span>数据源</span>
            <select
              aria-label="数据源"
              className="native-select wide-control"
              value={datasourceId}
              onChange={(event) => setDatasourceId(event.target.value)}
            >
              {datasources.map((datasource) => (
                <option key={datasource.id} value={datasource.id}>
                  {datasource.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field-block">
            <span>问题</span>
            <Input.TextArea
              rows={4}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="例如：统计昨天各业务线的订单量和转化率"
            />
          </label>
          <Space>
            <Button
              type="primary"
              loading={loading === 'generate'}
              disabled={!datasourceId || !question.trim()}
              onClick={generateSql}
            >
              生成 SQL
            </Button>
            <Button
              loading={loading === 'execute'}
              disabled={!datasourceId || !sql.trim()}
              onClick={executeSql}
            >
              执行 SQL
            </Button>
          </Space>
          <SqlEditor value={sql} onChange={setSql} />
        </Space>
        <aside className="history-panel">
          <Typography.Title level={3}>历史</Typography.Title>
          {history.length === 0 ? (
            <div className="empty-state compact">暂无历史</div>
          ) : (
            history.slice(0, 8).map((item) => (
              <button
                className="history-item"
                key={item.id}
                type="button"
                onClick={() => {
                  setQuestion(item.question);
                  setSql(item.final_sql || item.generated_sql);
                }}
              >
                {item.question || item.final_sql || item.generated_sql}
              </button>
            ))
          )}
        </aside>
      </div>
      <ResultTable result={result} />
    </section>
  );
}
