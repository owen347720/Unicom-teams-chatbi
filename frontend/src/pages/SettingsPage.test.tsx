import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SettingsPage } from './SettingsPage';
import { settingsApi } from '../services/api';

vi.mock('../services/api', () => ({
  settingsApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.mocked(settingsApi.get).mockResolvedValue({
      sql_timeout: 60,
      max_result_rows: 1000,
      log_level: 'INFO',
    });
    vi.mocked(settingsApi.update).mockResolvedValue({
      message: 'ok',
      updated_fields: ['sql_timeout', 'max_result_rows'],
    });
  });

  it('loads and saves editable runtime settings', async () => {
    render(<SettingsPage />);

    expect(await screen.findByDisplayValue('60')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('SQL 超时秒数'), { target: { value: '45' } });
    fireEvent.change(screen.getByLabelText('最大返回行数'), { target: { value: '500' } });
    fireEvent.click(screen.getByRole('button', { name: '保存设置' }));

    await waitFor(() =>
      expect(settingsApi.update).toHaveBeenCalledWith({
        sql_timeout: 45,
        max_result_rows: 500,
      }),
    );
  });
});
