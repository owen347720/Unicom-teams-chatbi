import { Alert, Button, Descriptions, Input, Space, Typography } from 'antd';
import { useEffect, useState } from 'react';
import { settingsApi } from '../services/api';

export function SettingsPage() {
  const [sqlTimeout, setSqlTimeout] = useState(60);
  const [maxResultRows, setMaxResultRows] = useState(1000);
  const [logLevel, setLogLevel] = useState('INFO');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    settingsApi
      .get()
      .then((config) => {
        setSqlTimeout(config.sql_timeout);
        setMaxResultRows(config.max_result_rows);
        setLogLevel(config.log_level || 'INFO');
      })
      .catch((error) => setNotice(error instanceof Error ? error.message : '加载配置失败'));
  }, []);

  async function saveSettings() {
    await settingsApi.update({
      sql_timeout: sqlTimeout,
      max_result_rows: maxResultRows,
    });
    setNotice('设置已保存');
  }

  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>系统设置</Typography.Title>
          <Typography.Paragraph>查看运行参数和部署配置，敏感信息通过环境变量维护。</Typography.Paragraph>
        </div>
      </div>
      {notice ? <Alert className="section-alert" type="info" message={notice} showIcon /> : null}
      <div className="form-grid settings-form">
        <label className="field-block">
          <span>SQL 超时秒数</span>
          <Input
            aria-label="SQL 超时秒数"
            type="number"
            value={sqlTimeout}
            onChange={(event) => setSqlTimeout(Number(event.target.value))}
          />
        </label>
        <label className="field-block">
          <span>最大返回行数</span>
          <Input
            aria-label="最大返回行数"
            type="number"
            value={maxResultRows}
            onChange={(event) => setMaxResultRows(Number(event.target.value))}
          />
        </label>
        <label className="field-block">
          <span>日志级别</span>
          <Input value={logLevel} readOnly />
        </label>
        <Space align="end">
          <Button type="primary" onClick={saveSettings}>
            保存设置
          </Button>
        </Space>
      </div>
      <Descriptions
        bordered
        column={1}
        items={[
          { key: 'api', label: 'Backend API', children: '/api/v1' },
          { key: 'deploy', label: '部署方式', children: 'Docker Compose' },
          { key: 'release', label: '交付模式', children: '离线镜像包 + release compose' },
        ]}
      />
    </section>
  );
}
