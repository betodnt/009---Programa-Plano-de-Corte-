CREATE TABLE IF NOT EXISTS operators (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS machines (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operations (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  operation_id CHAR(32) NOT NULL UNIQUE,
  pedido VARCHAR(80) NOT NULL,
  operator_id BIGINT NOT NULL,
  machine_id BIGINT NOT NULL,
  retalho VARCHAR(120) NULL,
  saida VARCHAR(255) NOT NULL,
  tipo VARCHAR(50) NULL,
  started_at DATETIME NOT NULL,
  finished_at DATETIME NULL,
  elapsed_seconds INT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'started',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_operations_operator FOREIGN KEY (operator_id) REFERENCES operators(id),
  CONSTRAINT fk_operations_machine FOREIGN KEY (machine_id) REFERENCES machines(id),
  INDEX idx_operations_machine_status (machine_id, status),
  INDEX idx_operations_started_at (started_at),
  INDEX idx_operations_saida (saida)
);

CREATE TABLE IF NOT EXISTS machine_locks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  machine_id BIGINT NOT NULL,
  saida VARCHAR(255) NOT NULL,
  operation_id CHAR(32) NOT NULL,
  operator_id BIGINT NOT NULL,
  owner_id VARCHAR(120) NOT NULL,
  heartbeat_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_locks_machine FOREIGN KEY (machine_id) REFERENCES machines(id),
  CONSTRAINT fk_locks_operator FOREIGN KEY (operator_id) REFERENCES operators(id),
  UNIQUE KEY uq_machine_saida (machine_id, saida),
  INDEX idx_locks_heartbeat (heartbeat_at)
);

CREATE TABLE IF NOT EXISTS settings (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  scope VARCHAR(50) NOT NULL DEFAULT 'global',
  `key` VARCHAR(100) NOT NULL,
  `value` TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_scope_key (scope, `key`)
);
