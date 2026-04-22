-- v6 canonical PostgreSQL migration for interface-device mappings,
-- interface message logs, and autoverification tables.

create table if not exists device_test_map (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id) on delete cascade,
    incoming_test_code text not null,
    test_catalog_id uuid not null references test_catalog(id),
    default_unit_ucum text null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique(device_id, incoming_test_code)
);

create index if not exists idx_device_test_map_device_code on device_test_map(device_id, incoming_test_code);

create table if not exists interface_message_log (
    id uuid primary key default gen_random_uuid(),
    protocol text not null,
    direction text not null check (direction in ('inbound','outbound')),
    message_type text not null,
    control_id text null,
    related_entity_type text null,
    related_entity_id uuid null,
    payload text not null,
    processed_ok boolean not null,
    error_text text null,
    created_at timestamptz not null default now()
);

create index if not exists idx_interface_message_control on interface_message_log(protocol, direction, message_type, control_id);

create table if not exists autoverification_rule (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    active boolean not null default true,
    priority int not null default 100,
    test_catalog_id uuid null references test_catalog(id),
    device_id uuid null references device(id),
    specimen_type_code text null,
    rule_type text not null check (rule_type in ('basic','delta')),
    condition_json jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists autoverification_run (
    id uuid primary key default gen_random_uuid(),
    observation_id uuid not null references observation(id) on delete cascade,
    rule_id uuid null references autoverification_rule(id),
    decision text not null check (decision in ('pass','fail','auto_finalized','held')),
    reasons_json jsonb not null default '[]'::jsonb,
    evaluated_at timestamptz not null,
    created_task_id uuid null references task_work(id)
);

create index if not exists idx_autoverification_rule_scope on autoverification_rule(test_catalog_id, device_id, specimen_type_code, active);
create index if not exists idx_autoverification_run_observation on autoverification_run(observation_id, evaluated_at desc);
