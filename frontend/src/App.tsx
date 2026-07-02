import { DatabaseOutlined, ExperimentOutlined, MessageOutlined, SettingOutlined } from '@ant-design/icons';
import { Button, ConfigProvider, Layout, Space, Typography } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { useState } from 'react';
import { AskPage } from './pages/AskPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { SettingsPage } from './pages/SettingsPage';
import { TrainingPage } from './pages/TrainingPage';

const { Header, Content } = Layout;

type SectionKey = 'ask' | 'datasources' | 'training' | 'settings';

const sections = [
  { key: 'ask', label: '问数', icon: <MessageOutlined /> },
  { key: 'datasources', label: '数据源', icon: <DatabaseOutlined /> },
  { key: 'training', label: '训练', icon: <ExperimentOutlined /> },
  { key: 'settings', label: '设置', icon: <SettingOutlined /> },
] satisfies Array<{ key: SectionKey; label: string; icon: React.ReactNode }>;

function renderSection(section: SectionKey) {
  switch (section) {
    case 'datasources':
      return <DataSourcesPage />;
    case 'training':
      return <TrainingPage />;
    case 'settings':
      return <SettingsPage />;
    case 'ask':
    default:
      return <AskPage />;
  }
}

export default function App() {
  const [activeSection, setActiveSection] = useState<SectionKey>('ask');

  return (
    <ConfigProvider
      locale={zhCN}
      wave={{ disabled: true }}
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
              <Button
                key={section.key}
                icon={section.icon}
                type={activeSection === section.key ? 'primary' : 'default'}
                onClick={() => setActiveSection(section.key)}
              >
                {section.label}
              </Button>
            ))}
          </Space>
        </Header>
        <Content className="app-content">{renderSection(activeSection)}</Content>
      </Layout>
    </ConfigProvider>
  );
}
