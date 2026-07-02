import { Alert, Button, Input, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { datasourceApi, trainingApi } from '../services/api';
import type { Datasource, TrainingData, TrainingPayload } from '../types';

const emptyForm: TrainingPayload = {
  datasource_id: '',
  question: '',
  sql: '',
};

export function TrainingPage() {
  const [datasources, setDatasources] = useState<Datasource[]>([]);
  const [items, setItems] = useState<TrainingData[]>([]);
  const [pending, setPending] = useState<TrainingData[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<TrainingPayload>(emptyForm);
  const [notice, setNotice] = useState('');

  async function loadTrainingData() {
    const [datasourceResponse, trainingResponse, pendingResponse] = await Promise.all([
      datasourceApi.list(),
      trainingApi.list(),
      trainingApi.pending(),
    ]);
    setDatasources(datasourceResponse.items);
    setItems(trainingResponse.items);
    setPending(pendingResponse.items);
    setForm((current) => ({
      ...current,
      datasource_id: current.datasource_id || datasourceResponse.items[0]?.id || '',
    }));
  }

  useEffect(() => {
    loadTrainingData().catch((error) => setNotice(error instanceof Error ? error.message : '加载训练数据失败'));
  }, []);

  function updateForm<K extends keyof TrainingPayload>(key: K, value: TrainingPayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function saveTrainingData() {
    await trainingApi.add(form);
    setForm({ ...emptyForm, datasource_id: datasources[0]?.id || '' });
    setFormOpen(false);
    setNotice('训练数据已保存');
    await loadTrainingData();
  }

  async function approveTrainingData(id: string) {
    await trainingApi.approve(id);
    setNotice('训练数据已审核');
    await loadTrainingData();
  }

  async function removeTrainingData(id: string) {
    await trainingApi.remove(id);
    setNotice('训练数据已删除');
    await loadTrainingData();
  }

  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>训练数据</Typography.Title>
          <Typography.Paragraph>维护自然语言问题和 SQL 示例，提升后续生成质量。</Typography.Paragraph>
        </div>
        <Button type="primary" onClick={() => setFormOpen((value) => !value)}>
          新增训练数据
        </Button>
      </div>
      {notice ? <Alert className="section-alert" type="info" message={notice} showIcon /> : null}
      {formOpen ? (
        <div className="form-grid training-form">
          <label className="field-block">
            <span>数据源</span>
            <select
              aria-label="数据源"
              className="native-select"
              value={form.datasource_id}
              onChange={(event) => updateForm('datasource_id', event.target.value)}
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
            <Input value={form.question} onChange={(event) => updateForm('question', event.target.value)} />
          </label>
          <label className="field-block form-span">
            <span>SQL</span>
            <Input.TextArea rows={4} value={form.sql} onChange={(event) => updateForm('sql', event.target.value)} />
          </label>
          <Space align="end">
            <Button type="primary" onClick={saveTrainingData}>
              保存训练数据
            </Button>
          </Space>
        </div>
      ) : null}
      <div className="split-panel">
        <div>
          <Typography.Title level={3}>已批准</Typography.Title>
          {items.length === 0 ? (
            <div className="empty-state compact">暂无训练数据</div>
          ) : (
            <div className="data-list">
              {items.map((item) => (
                <article className="data-row" key={item.id}>
                  <div>
                    <strong>{item.question}</strong>
                    <span>{item.sql}</span>
                  </div>
                  <Button danger onClick={() => removeTrainingData(item.id)}>
                    删除
                  </Button>
                </article>
              ))}
            </div>
          )}
        </div>
        <div>
          <Typography.Title level={3}>待审核</Typography.Title>
          {pending.length === 0 ? (
            <div className="empty-state compact">暂无待审核数据</div>
          ) : (
            <div className="data-list">
              {pending.map((item) => (
                <article className="data-row" key={item.id}>
                  <div>
                    <strong>{item.question}</strong>
                    <span>{item.sql}</span>
                  </div>
                  <Button onClick={() => approveTrainingData(item.id)}>审核</Button>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
