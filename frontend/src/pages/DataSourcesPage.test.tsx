import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DataSourcesPage } from './DataSourcesPage';
import { datasourceApi } from '../services/api';

vi.mock('../services/api', () => ({
  datasourceApi: {
    list: vi.fn(),
    add: vi.fn(),
    test: vi.fn(),
    remove: vi.fn(),
  },
}));

describe('DataSourcesPage', () => {
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
          tables_count: 12,
        },
      ],
    });
    vi.mocked(datasourceApi.add).mockResolvedValue({
      id: 'ds-2',
      message: 'ok',
      tables_extracted: 3,
    });
    vi.mocked(datasourceApi.test).mockResolvedValue({
      success: true,
      message: 'Connection successful',
      tables_count: 12,
    });
    vi.mocked(datasourceApi.remove).mockResolvedValue({ id: 'ds-1', message: 'ok' });
  });

  it('lists datasources and supports add/test/delete actions', async () => {
    render(<DataSourcesPage />);

    expect(await screen.findByText('订单库')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /测\s*试/ }));
    await waitFor(() => expect(datasourceApi.test).toHaveBeenCalledWith('ds-1'));

    fireEvent.click(screen.getByRole('button', { name: '新增数据源' }));
    fireEvent.change(screen.getByLabelText('名称'), { target: { value: '用户库' } });
    fireEvent.change(screen.getByLabelText('主机'), { target: { value: '10.0.0.8' } });
    fireEvent.change(screen.getByLabelText('端口'), { target: { value: '5432' } });
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'readonly' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'secret' } });
    fireEvent.change(screen.getByLabelText('数据库'), { target: { value: 'analytics' } });
    fireEvent.change(screen.getByLabelText('类型'), { target: { value: 'postgresql' } });
    fireEvent.click(screen.getByRole('button', { name: '保存数据源' }));

    await waitFor(() =>
      expect(datasourceApi.add).toHaveBeenCalledWith({
        name: '用户库',
        type: 'postgresql',
        host: '10.0.0.8',
        port: 5432,
        username: 'readonly',
        password: 'secret',
        database: 'analytics',
      }),
    );

    fireEvent.click(screen.getByRole('button', { name: /删\s*除/ }));
    await waitFor(() => expect(datasourceApi.remove).toHaveBeenCalledWith('ds-1'));
  });
});
