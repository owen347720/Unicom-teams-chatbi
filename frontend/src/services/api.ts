import axios from 'axios';
import type {
  Datasource,
  DatasourcePayload,
  ExecuteSqlRequest,
  ExecuteSqlResponse,
  GenerateSqlRequest,
  GenerateSqlResponse,
  ListResponse,
  QueryHistory,
  SystemConfig,
  TrainingData,
  TrainingPayload,
} from '../types';

type RawListResponse<T> = {
  total?: number;
  items?: T[];
};

export function buildApiBaseUrl(value = import.meta.env.VITE_API_BASE_URL): string {
  const baseUrl = value?.trim() || '/api/v1';
  return baseUrl.replace(/\/+$/, '');
}

export function normalizeListResponse<T>(response: RawListResponse<T>): ListResponse<T> {
  const items = response.items ?? [];
  return {
    total: response.total ?? items.length,
    items,
  };
}

export const apiClient = axios.create({
  baseURL: buildApiBaseUrl(),
  timeout: 60_000,
});

export const datasourceApi = {
  async list(): Promise<ListResponse<Datasource>> {
    const { data } = await apiClient.get<RawListResponse<Datasource>>('/datasources/list');
    return normalizeListResponse(data);
  },

  async add(payload: DatasourcePayload): Promise<{ id: string; message: string; tables_extracted: number }> {
    const { data } = await apiClient.post('/datasources/add', payload);
    return data;
  },

  async update(id: string, payload: Partial<Omit<DatasourcePayload, 'type' | 'database'>>): Promise<{ id: string; message: string }> {
    const { data } = await apiClient.put(`/datasources/${id}`, payload);
    return data;
  },

  async remove(id: string): Promise<{ id: string; message: string }> {
    const { data } = await apiClient.delete(`/datasources/${id}`);
    return data;
  },

  async test(id: string): Promise<{ success: boolean; message: string; tables_count: number }> {
    const { data } = await apiClient.post(`/datasources/${id}/test`);
    return data;
  },
};

export const askApi = {
  async generateSql(payload: GenerateSqlRequest): Promise<GenerateSqlResponse> {
    const { data } = await apiClient.post<GenerateSqlResponse>('/ask/generate-sql', payload);
    return data;
  },

  async executeSql(payload: ExecuteSqlRequest): Promise<ExecuteSqlResponse> {
    const { data } = await apiClient.post<ExecuteSqlResponse>('/ask/execute-sql', payload);
    return data;
  },

  async history(datasourceId?: string): Promise<ListResponse<QueryHistory>> {
    const { data } = await apiClient.get<RawListResponse<QueryHistory>>('/ask/history', {
      params: datasourceId ? { datasource_id: datasourceId } : undefined,
    });
    return normalizeListResponse(data);
  },
};

export const trainingApi = {
  async list(params?: { datasource_id?: string; source?: string; is_approved?: boolean }): Promise<ListResponse<TrainingData>> {
    const { data } = await apiClient.get<RawListResponse<TrainingData>>('/training/list', { params });
    return normalizeListResponse(data);
  },

  async add(payload: TrainingPayload): Promise<{ id: string; message: string }> {
    const { data } = await apiClient.post('/training/add', payload);
    return data;
  },

  async update(id: string, payload: Partial<Pick<TrainingPayload, 'question' | 'sql'>>): Promise<{ id: string; message: string }> {
    const { data } = await apiClient.put(`/training/${id}`, payload);
    return data;
  },

  async remove(id: string): Promise<{ id: string; message: string }> {
    const { data } = await apiClient.delete(`/training/${id}`);
    return data;
  },

  async pending(): Promise<ListResponse<TrainingData>> {
    const { data } = await apiClient.get<RawListResponse<TrainingData>>('/training/pending');
    return normalizeListResponse(data);
  },

  async approve(id: string): Promise<{ id: string; message: string; is_approved: boolean }> {
    const { data } = await apiClient.post(`/training/approve/${id}`);
    return data;
  },
};

export const settingsApi = {
  async get(): Promise<SystemConfig> {
    const { data } = await apiClient.get<SystemConfig>('/settings/config');
    return data;
  },

  async update(payload: Partial<Pick<SystemConfig, 'sql_timeout' | 'max_result_rows'>>): Promise<{ message: string; updated_fields: string[] }> {
    const { data } = await apiClient.put('/settings/config', payload);
    return data;
  },
};
