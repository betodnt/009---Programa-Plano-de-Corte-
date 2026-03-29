import { invoke } from "@tauri-apps/api/core";
import type {
  BackendStatus,
  BootstrapData,
  BootstrapResult,
  DatabaseCheckResult,
  FinishOperationResult,
  LockHeartbeatResult,
  MonitorSnapshot,
  RuntimeConfig,
  StartOperationInput,
  StartOperationResult,
  SearchCncInput,
  SearchCncResult,
  OpenPdfInput
} from "../types";

type FinishOperationInput = {
  operation_id: string;
};

type LockHeartbeatInput = {
  operation_id: string;
};

export const tauriClient = {
  getRuntimeConfig() {
    return invoke<RuntimeConfig>("get_runtime_config");
  },
  getBackendStatus() {
    return invoke<BackendStatus>("get_backend_status");
  },
  testDatabaseConnection() {
    return invoke<DatabaseCheckResult>("test_database_connection");
  },
  bootstrapDatabase() {
    return invoke<BootstrapResult>("bootstrap_database");
  },
  getBootstrapData() {
    return invoke<BootstrapData>("get_bootstrap_data");
  },
  startOperation(input: StartOperationInput) {
    return invoke<StartOperationResult>("start_operation", { input });
  },
  finishOperation(input: FinishOperationInput) {
    return invoke<FinishOperationResult>("finish_operation", { input });
  },
  touchOperationLock(input: LockHeartbeatInput) {
    return invoke<LockHeartbeatResult>("touch_operation_lock", { input });
  },
  getMonitorSnapshot() {
    return invoke<MonitorSnapshot>("get_monitor_snapshot");
  },
  searchCncFiles(input: SearchCncInput) {
    return invoke<SearchCncResult>("search_cnc_files", { input });
  },
  openPdf(input: OpenPdfInput) {
    return invoke<boolean>("open_pdf", { input });
  }
};
