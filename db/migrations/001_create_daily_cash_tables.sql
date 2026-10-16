-- 001_create_daily_cash_tables.sql
-- Postgres migration for Daily Cash Transaction Engine

BEGIN;

-- daily_cash_transactions
CREATE TABLE IF NOT EXISTS daily_cash_transactions (
  id bigserial PRIMARY KEY,
  txn_ref text UNIQUE,
  source text,
  source_message_ref text,
  source_bridge text,
  employee_id integer,
  employee_name text,
  employee_phone text,
  payment_method text,
  amount numeric(12,2) NOT NULL,
  currency text DEFAULT 'BDT',
  reference_number text,
  transaction_date date NOT NULL DEFAULT CURRENT_DATE,
  transaction_time timestamptz,
  created_by text,
  approved_by text,
  approval_status text DEFAULT 'pending',
  transaction_status text DEFAULT 'pending',
  is_reconciled boolean DEFAULT false,
  reconciled_at timestamptz,
  notes text,
  attachments jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_daily_cash_emp ON daily_cash_transactions(employee_id);
CREATE INDEX IF NOT EXISTS idx_daily_cash_date ON daily_cash_transactions(transaction_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_source_ref ON daily_cash_transactions (source, source_message_ref) WHERE source_message_ref IS NOT NULL;

-- daily_employee_ledger
CREATE TABLE IF NOT EXISTS daily_employee_ledger (
  id bigserial PRIMARY KEY,
  employee_id integer NOT NULL,
  ledger_date date NOT NULL,
  opening_balance numeric(12,2) DEFAULT 0,
  credits numeric(12,2) DEFAULT 0,
  debits numeric(12,2) DEFAULT 0,
  closing_balance numeric(12,2) DEFAULT 0,
  last_txn_id bigint,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(employee_id, ledger_date)
);
CREATE INDEX IF NOT EXISTS idx_ledger_emp_date ON daily_employee_ledger(employee_id, ledger_date);

-- daily_import_jobs
CREATE TABLE IF NOT EXISTS daily_import_jobs (
  id bigserial PRIMARY KEY,
  filename text,
  uploaded_by text,
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  row_count integer,
  success_count integer,
  failure_count integer,
  errors jsonb,
  importer_settings jsonb
);

-- daily_audit_logs
CREATE TABLE IF NOT EXISTS daily_audit_logs (
  id bigserial PRIMARY KEY,
  txn_id bigint,
  action text NOT NULL,
  actor text,
  payload jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

COMMIT;
