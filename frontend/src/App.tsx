import { DatabaseOutlined, ExperimentOutlined, MessageOutlined, SettingOutlined } from '@ant-design/icons';
import { Button, ConfigProvider, Layout, Space, Typography } from 'antd';
import zhCN from 'antd/locale/zh_CN';

const { Header, Content } = Layout;

const sections = [
  { key: 'ask', label: '问数', icon: <MessageOutlined /> },
  { key: 'datasources', label: '数据源', icon: <DatabaseOutlined /> },
  { key: 'training', label: '训练', icon: <ExperimentOutlined /> },
  { key: 'settings', label: '设置', icon: <SettingOutlined /> },
];

export default function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1f6f5b',
          borderRadius: 6,
          fontFamily:
            '"Avenir Next", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif',
        },
      }}
    >
      <Layout className="app-shell">
        <Header className="app-header">
          <div>
            <Typography.Title level={1} className="app-title">
              Text2SQL
            </Typography.Title>
            <Typography.Text className="app-subtitle">团队问数工作台</Typography.Text>
          </div>
          <Space size={8} wrap>
            {sections.map((section) => (
              <Button key={section.key} icon={section.icon}>
                {section.label}
              </Button>
            ))}
          </Space>
        </Header>
        <Content className="app-content">
          <section className="workspace-panel">
            <Typography.Title level={2}>问数</Typography.Title>
            <Typography.Paragraph>
              选择数据源，输入自然语言问题，生成可审阅 SQL 后执行查询。
            </Typography.Paragraph>
          </section>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}
