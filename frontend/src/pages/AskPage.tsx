import { Button, Input, Space, Typography } from 'antd';

export function AskPage() {
  return (
    <section className="workspace-panel">
      <div className="page-heading">
        <div>
          <Typography.Title level={2}>问数</Typography.Title>
          <Typography.Paragraph>选择数据源，输入自然语言问题，生成可审阅 SQL 后执行查询。</Typography.Paragraph>
        </div>
      </div>
      <Space direction="vertical" size={12} className="full-width">
        <Input className="wide-control" placeholder="选择数据源" readOnly />
        <Input.TextArea rows={4} placeholder="例如：统计昨天各业务线的订单量和转化率" />
        <Space>
          <Button type="primary">生成 SQL</Button>
          <Button>执行 SQL</Button>
        </Space>
      </Space>
    </section>
  );
}
