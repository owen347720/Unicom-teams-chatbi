import { describe, expect, it } from 'vitest';
import { buildApiBaseUrl, normalizeListResponse } from './api';

describe('api helpers', () => {
  it('uses /api/v1 as the default backend base URL', () => {
    expect(buildApiBaseUrl()).toBe('/api/v1');
  });

  it('removes trailing slashes from custom backend base URLs', () => {
    expect(buildApiBaseUrl('http://localhost:8000/api/v1/')).toBe('http://localhost:8000/api/v1');
  });

  it('normalizes list responses with missing totals', () => {
    expect(normalizeListResponse({ items: [{ id: 'a' }] })).toEqual({
      total: 1,
      items: [{ id: 'a' }],
    });
  });
});
