import { fireEvent, render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import App from './App';

vi.mock('./pages/AskPage', () => ({
  AskPage: () => <section><h2>问数</h2></section>,
}));

vi.mock('./pages/DataSourcesPage', () => ({
  DataSourcesPage: () => (
    <section>
      <h2>数据源管理</h2>
      <p>新增、测试和维护数据库连接</p>
    </section>
  ),
}));

vi.mock('./pages/TrainingPage', () => ({
  TrainingPage: () => <section><h2>训练数据</h2></section>,
}));

vi.mock('./pages/SettingsPage', () => ({
  SettingsPage: () => <section><h2>系统设置</h2></section>,
}));

describe('App', () => {
  it('renders the Text2SQL workspace shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /Text2SQL/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /问数/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /数据源/i })).toBeInTheDocument();
  });

  it('switches between workspace sections', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /数据源/i }));

    expect(await screen.findByRole('heading', { name: /数据源管理/i })).toBeInTheDocument();
    expect(screen.getByText(/新增、测试和维护数据库连接/i)).toBeInTheDocument();
  });
});
