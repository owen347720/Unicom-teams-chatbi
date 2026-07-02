import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AskPage } from './AskPage';
import { askApi, datasourceApi } from '../services/api';

vi.mock('../services/api', () => ({
  datasourceApi: {
    list: vi.fn(),
  },
  askApi: {
    generateSql: vi.fn(),
    executeSql: vi.fn(),
    history: vi.fn(),
  },
}));

describe('AskPage', () => {
  beforeEach(() => {
    vi.mocked(datasourceApi.list).mockResolvedValue({
      total: 1,
      items: [
        {
          id: 'ds-1',
          name: '订单库',
          type: 'clickhouse',
          host: '127.0.0.1',
          port: 9000,
          database: 'default',
          username: 'default',
          is_active: true,
        },
      ],
    });
    vi.mocked(askApi.history).mockResolvedValue({ total: 0, items: [] });
    vi.mocked(askApi.generateSql).mockResolvedValue({
      sql: 'SELECT count(*) FROM orders',
      confidence: 0.87,
      related_training_data: [],
    });
    vi.mocked(askApi.executeSql).mockResolvedValue({
      columns: ['count'],
      rows: [[42]],
      row_count: 1,
      execution_time: 0.12,
    });
  });

  it('generates editable SQL and executes it', async () => {
    render(<AskPage />);

    await screen.findByRole('option', { name: '订单库' });
    fireEvent.change(screen.getByLabelText('数据源'), { target: { value: 'ds-1' } });
    fireEvent.change(screen.getByLabelText('问题'), { target: { value: '订单总数是多少' } });
    fireEvent.click(screen.getByRole('button', { name: '生成 SQL' }));

    expect(await screen.findByDisplayValue('SELECT count(*) FROM orders')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '执行 SQL' }));

    await waitFor(() => {
      expect(askApi.executeSql).toHaveBeenCalledWith({
        datasource_id: 'ds-1',
        sql: 'SELECT count(*) FROM orders',
      });
    });
    expect(await screen.findByText('42')).toBeInTheDocument();
    expect(screen.getByText(/1 行/)).toBeInTheDocument();
  });
});
