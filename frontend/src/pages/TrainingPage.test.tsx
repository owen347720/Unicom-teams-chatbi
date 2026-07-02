import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TrainingPage } from './TrainingPage';
import { datasourceApi, trainingApi } from '../services/api';

vi.mock('../services/api', () => ({
  datasourceApi: {
    list: vi.fn(),
  },
  trainingApi: {
    list: vi.fn(),
    add: vi.fn(),
    pending: vi.fn(),
    approve: vi.fn(),
    remove: vi.fn(),
  },
}));

describe('TrainingPage', () => {
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
    vi.mocked(trainingApi.list).mockResolvedValue({
      total: 1,
      items: [
        {
          id: 'tr-1',
          datasource_id: 'ds-1',
          question: '订单总数',
          sql: 'SELECT count(*) FROM orders',
          source: 'manual',
          is_approved: true,
        },
      ],
    });
    vi.mocked(trainingApi.pending).mockResolvedValue({
      total: 1,
      items: [
        {
          id: 'tr-2',
          datasource_id: 'ds-1',
          question: '昨天订单',
          sql: 'SELECT * FROM orders',
          source: 'auto',
          is_approved: false,
        },
      ],
    });
    vi.mocked(trainingApi.add).mockResolvedValue({ id: 'tr-3', message: 'ok' });
    vi.mocked(trainingApi.approve).mockResolvedValue({ id: 'tr-2', message: 'ok', is_approved: true });
    vi.mocked(trainingApi.remove).mockResolvedValue({ id: 'tr-1', message: 'ok' });
  });

  it('manages manual and pending training data', async () => {
    render(<TrainingPage />);

    expect(await screen.findByText('订单总数')).toBeInTheDocument();
    expect(await screen.findByText('昨天订单')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '新增训练数据' }));
    fireEvent.change(screen.getByLabelText('数据源'), { target: { value: 'ds-1' } });
    fireEvent.change(screen.getByLabelText('问题'), { target: { value: '用户数' } });
    fireEvent.change(screen.getByLabelText('SQL'), { target: { value: 'SELECT count(*) FROM users' } });
    fireEvent.click(screen.getByRole('button', { name: '保存训练数据' }));

    await waitFor(() =>
      expect(trainingApi.add).toHaveBeenCalledWith({
        datasource_id: 'ds-1',
        question: '用户数',
        sql: 'SELECT count(*) FROM users',
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: /审\s*核/ }));
    await waitFor(() => expect(trainingApi.approve).toHaveBeenCalledWith('tr-2'));

    fireEvent.click(screen.getByRole('button', { name: /删\s*除/ }));
    await waitFor(() => expect(trainingApi.remove).toHaveBeenCalledWith('tr-1'));
  });
});
