export type DatabaseType = 'clickhouse' | 'postgresql' | 'mysql';

export interface ListResponse<T> {
  total: number;
  items: T[];
}

export interface Datasource {
  id: string;
  name: string;
  type: DatabaseType;
  host: string;
  port: number;
  database: string;
  username: string;
  is_active: boolean;
  tables_count?: number;
  created_at?: string | null;
}

export interface DatasourcePayload {
  name: string;
  type: DatabaseType;
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
}

export interface GenerateSqlRequest {
  datasource_id: string;
  question: string;
}

export interface GenerateSqlResponse {
  sql: string;
  confidence?: number;
  related_training_data: unknown[];
}

export interface ExecuteSqlRequest {
  datasource_id: string;
  sql: string;
  timeout?: number;
}

export interface ExecuteSqlResponse {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_time: number;
}

export interface QueryHistory {
  id: string;
  datasource_id: string;
  question: string;
  generated_sql: string;
  final_sql: string;
  executed: boolean;
  result_rows: number;
  execution_time: number;
  created_at?: string | null;
}

export interface TrainingData {
  id: string;
  datasource_id: string;
  question: string;
  sql: string;
  source: 'manual' | 'auto';
  is_approved: boolean;
  created_at?: string | null;
}

export interface TrainingPayload {
  datasource_id: string;
  question: string;
  sql: string;
}

export interface SystemConfig {
  sql_timeout: number;
  max_result_rows: number;
  log_level?: string;
}
