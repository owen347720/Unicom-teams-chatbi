import { Button, Typography } from 'antd';

export function TrainingPage() {
  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>训练数据</Typography.Title>
          <Typography.Paragraph>维护自然语言问题和 SQL 示例，提升后续生成质量。</Typography.Paragraph>
        </div>
        <Button type="primary">新增训练数据</Button>
      </div>
      <div className="empty-state">暂无训练数据</div>
    </section>
  );
}
