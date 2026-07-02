import { Alert, Button, Input, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { datasourceApi } from '../services/api';
import type { DatabaseType, Datasource, DatasourcePayload } from '../types';

const emptyForm: DatasourcePayload = {
  name: '',
  type: 'clickhouse',
  host: '',
  port: 9000,
  username: '',
  password: '',
  database: '',
};

export function DataSourcesPage() {
  const [datasources, setDatasources] = useState<Datasource[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<DatasourcePayload>(emptyForm);
  const [notice, setNotice] = useState('');

  async function loadDatasources() {
    const response = await datasourceApi.list();
    setDatasources(response.items);
  }

  useEffect(() => {
    loadDatasources().catch((error) => setNotice(error instanceof Error ? error.message : '加载数据源失败'));
  }, []);

  function updateForm<K extends keyof DatasourcePayload>(key: K, value: DatasourcePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function saveDatasource() {
    await datasourceApi.add(form);
    setForm(emptyForm);
    setFormOpen(false);
    setNotice('数据源已保存');
    await loadDatasources();
  }

  async function testDatasource(id: string) {
    const result = await datasourceApi.test(id);
    setNotice(result.message);
  }

  async function removeDatasource(id: string) {
    await datasourceApi.remove(id);
    setNotice('数据源已删除');
    await loadDatasources();
  }

  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>数据源管理</Typography.Title>
          <Typography.Paragraph>新增、测试和维护数据库连接，保存后用于 SQL 生成与执行。</Typography.Paragraph>
        </div>
        <Button type="primary" onClick={() => setFormOpen((value) => !value)}>
          新增数据源
        </Button>
      </div>
      {notice ? <Alert className="section-alert" type="info" message={notice} showIcon /> : null}
      {formOpen ? (
        <div className="form-grid">
          <label className="field-block">
            <span>名称</span>
            <Input value={form.name} onChange={(event) => updateForm('name', event.target.value)} />
          </label>
          <label className="field-block">
            <span>类型</span>
            <select
              aria-label="类型"
              className="native-select"
              value={form.type}
              onChange={(event) => updateForm('type', event.target.value as DatabaseType)}
            >
              <option value="clickhouse">ClickHouse</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
            </select>
          </label>
          <label className="field-block">
            <span>主机</span>
            <Input value={form.host} onChange={(event) => updateForm('host', event.target.value)} />
          </label>
          <label className="field-block">
            <span>端口</span>
            <Input
              type="number"
              value={form.port}
              onChange={(event) => updateForm('port', Number(event.target.value))}
            />
          </label>
          <label className="field-block">
            <span>用户名</span>
            <Input value={form.username} onChange={(event) => updateForm('username', event.target.value)} />
          </label>
          <label className="field-block">
            <span>密码</span>
            <Input.Password value={form.password} onChange={(event) => updateForm('password', event.target.value)} />
          </label>
          <label className="field-block">
            <span>数据库</span>
            <Input value={form.database} onChange={(event) => updateForm('database', event.target.value)} />
          </label>
          <Space align="end">
            <Button type="primary" onClick={saveDatasource}>
              保存数据源
            </Button>
          </Space>
        </div>
      ) : null}
      {datasources.length === 0 ? (
        <div className="empty-state">暂无数据源</div>
      ) : (
        <div className="data-list">
          {datasources.map((datasource) => (
            <article className="data-row" key={datasource.id}>
              <div>
                <strong>{datasource.name}</strong>
                <span>
                  {datasource.type} · {datasource.host}:{datasource.port} · {datasource.database}
                </span>
              </div>
              <Space>
                <Button onClick={() => testDatasource(datasource.id)}>测试</Button>
                <Button danger onClick={() => removeDatasource(datasource.id)}>
                  删除
                </Button>
              </Space>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
