export type RuntimeConfig = {
  app_env: string;
  machine_name: string;
  database_url_masked: string;
};

export type BackendStatus = {
  app_name: string;
  app_env: string;
  database_configured: boolean;
  database_connected: boolean;
  machine_name: string;
  checked_at: string;
};

export type DatabaseCheckResult = {
  ok: boolean;
  message: string;
  checked_at: string;
};

export type MachineSummary = {
  id: number;
  name: string;
  is_active: boolean;
};

export type OperatorSummary = {
  id: number;
  name: string;
};

export type OperationSummary = {
  operation_id: string;
  pedido: string;
  operator_name: string;
  machine_name: string;
  saida: string;
  tipo: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  elapsed_seconds: number | null;
};

export type ActiveLockSummary = {
  machine_name: string;
  saida: string;
  operator_name: string;
  operation_id: string;
  heartbeat_at: string;
};

export type MonitorSnapshot = {
  active_operations: OperationSummary[];
  active_locks: ActiveLockSummary[];
  machines: MachineSummary[];
  generated_at: string;
};

export type BootstrapResult = {
  ok: boolean;
  message: string;
};

export type StartOperationInput = {
  pedido: string;
  operador: string;
  maquina: string;
  retalho?: string;
  saida: string;
  tipo?: string;
  owner_id?: string;
};

export type StartOperationResult = {
  operation_id: string;
  status: string;
  message: string;
};

export type FinishOperationResult = {
  operation_id: string;
  status: string;
  elapsed_seconds: number;
  message: string;
};

export type LockHeartbeatResult = {
  ok: boolean;
  message: string;
  heartbeat_at: string;
};

export type BootstrapData = {
  runtime: RuntimeConfig;
  machines: MachineSummary[];
  operators: OperatorSummary[];
  generated_at: string;
};

export type SearchCncInput = {
  pedido: string;
  tipo: string;
};

export type SearchCncResult = {
  files: string[];
};

export type OpenPdfInput = {
  cnc_filename: string;
};

