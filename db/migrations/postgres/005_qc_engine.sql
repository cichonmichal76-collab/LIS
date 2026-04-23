-- v10 canonical PostgreSQL migration for QC engine.

create table if not exists qc_material (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    manufacturer text null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists qc_lot (
    id uuid primary key default gen_random_uuid(),
    material_id uuid not null references qc_material(id),
    lot_no text not null,
    test_catalog_id uuid not null references test_catalog(id),
    device_id uuid null references device(id),
    unit_ucum text null,
    target_mean numeric null,
    target_sd numeric null,
    min_value numeric null,
    max_value numeric null,
    active boolean not null default true,
    expires_at timestamptz null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists qc_rule (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    active boolean not null default true,
    priority int not null default 100,
    test_catalog_id uuid null references test_catalog(id),
    device_id uuid null references device(id),
    rule_type text not null check (rule_type in ('range','westgard_12s','westgard_13s','westgard_22s')),
    params_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists qc_run (
    id uuid primary key default gen_random_uuid(),
    lot_id uuid not null references qc_lot(id),
    device_id uuid null references device(id),
    status text not null check (status in ('open','passed','warning','failed')),
    started_at timestamptz not null default now(),
    evaluated_at timestamptz null,
    reviewed_by_user_id uuid null references app_user(id),
    summary_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists qc_result (
    id uuid primary key default gen_random_uuid(),
    run_id uuid not null references qc_run(id) on delete cascade,
    test_catalog_id uuid not null references test_catalog(id),
    value_num numeric not null,
    unit_ucum text null,
    decision text null check (decision in ('pass','warning','fail')),
    z_score numeric null,
    warning_rules_json jsonb not null default '[]'::jsonb,
    failure_rules_json jsonb not null default '[]'::jsonb,
    observed_at timestamptz null,
    evaluated_at timestamptz null,
    raw_message_id uuid null references raw_instrument_message(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_qc_lot_scope on qc_lot(test_catalog_id, device_id, active);
create index if not exists idx_qc_lot_material on qc_lot(material_id, lot_no);
create index if not exists idx_qc_rule_scope on qc_rule(test_catalog_id, device_id, active);
create index if not exists idx_qc_run_lot_status on qc_run(lot_id, status, created_at desc);
create index if not exists idx_qc_run_device_status on qc_run(device_id, status, created_at desc);
create index if not exists idx_qc_result_run on qc_result(run_id, created_at desc);
create index if not exists idx_qc_result_test_eval on qc_result(test_catalog_id, evaluated_at desc);
