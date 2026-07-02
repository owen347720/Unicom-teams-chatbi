import { fireEvent, render, screen } from '@testing-library/react';
import App from './App';

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
