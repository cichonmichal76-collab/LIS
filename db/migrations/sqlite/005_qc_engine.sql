-- v10 canonical SQLite migration for QC engine.

create table if not exists qc_material (
    id text primary key,
    code text not null unique,
    name text not null,
    manufacturer text null,
    active integer not null default 1,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists qc_lot (
    id text primary key,
    material_id text not null references qc_material(id),
    lot_no text not null,
    test_catalog_id text not null references test_catalog(id),
    device_id text null references device(id),
    unit_ucum text null,
    target_mean real null,
    target_sd real null,
    min_value real null,
    max_value real null,
    active integer not null default 1,
    expires_at text null,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists qc_rule (
    id text primary key,
    name text not null,
    active integer not null default 1,
    priority integer not null default 100,
    test_catalog_id text null references test_catalog(id),
    device_id text null references device(id),
    rule_type text not null check (rule_type in ('range','westgard_12s','westgard_13s','westgard_22s')),
    params_json text not null default '{}',
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists qc_run (
    id text primary key,
    lot_id text not null references qc_lot(id),
    device_id text null references device(id),
    status text not null check (status in ('open','passed','warning','failed')),
    started_at text not null default current_timestamp,
    evaluated_at text null,
    reviewed_by_user_id text null references app_user(id),
    summary_json text not null default '{}',
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists qc_result (
    id text primary key,
    run_id text not null references qc_run(id) on delete cascade,
    test_catalog_id text not null references test_catalog(id),
    value_num real not null,
    unit_ucum text null,
    decision text null check (decision in ('pass','warning','fail')),
    z_score real null,
    warning_rules_json text not null default '[]',
    failure_rules_json text not null default '[]',
    observed_at text null,
    evaluated_at text null,
    raw_message_id text null references raw_instrument_message(id),
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create index if not exists idx_qc_lot_scope on qc_lot(test_catalog_id, device_id, active);
create index if not exists idx_qc_lot_material on qc_lot(material_id, lot_no);
create index if not exists idx_qc_rule_scope on qc_rule(test_catalog_id, device_id, active);
create index if not exists idx_qc_run_lot_status on qc_run(lot_id, status, created_at);
create index if not exists idx_qc_run_device_status on qc_run(device_id, status, created_at);
create index if not exists idx_qc_result_run on qc_result(run_id, created_at);
create index if not exists idx_qc_result_test_eval on qc_result(test_catalog_id, evaluated_at);
