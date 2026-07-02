import { Descriptions, Typography } from 'antd';

export function SettingsPage() {
  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>系统设置</Typography.Title>
          <Typography.Paragraph>查看运行参数和部署配置，敏感信息通过环境变量维护。</Typography.Paragraph>
        </div>
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
