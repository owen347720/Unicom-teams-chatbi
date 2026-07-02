import { Button, Typography } from 'antd';

export function DataSourcesPage() {
  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>数据源管理</Typography.Title>
          <Typography.Paragraph>新增、测试和维护数据库连接，保存后用于 SQL 生成与执行。</Typography.Paragraph>
        </div>
        <Button type="primary">新增数据源</Button>
      </div>
      <div className="empty-state">暂无数据源</div>
    </section>
  );
}
