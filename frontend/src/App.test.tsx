import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the Text2SQL workspace shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /Text2SQL/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /问数/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /数据源/i })).toBeInTheDocument();
  });
});
