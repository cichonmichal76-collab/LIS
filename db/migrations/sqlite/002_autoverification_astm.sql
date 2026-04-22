-- v6 canonical SQLite migration for interface-device mappings,
-- interface message logs, and autoverification tables.

create table if not exists device_test_map (
    id text primary key,
    device_id text not null references device(id) on delete cascade,
    incoming_test_code text not null,
    test_catalog_id text not null references test_catalog(id),
    default_unit_ucum text null,
    active integer not null default 1,
    created_at text not null default current_timestamp,
    unique(device_id, incoming_test_code)
);

create index if not exists idx_device_test_map_device_code on device_test_map(device_id, incoming_test_code);

create table if not exists interface_message_log (
    id text primary key,
    protocol text not null,
    direction text not null check (direction in ('inbound','outbound')),
    message_type text not null,
    control_id text null,
    related_entity_type text null,
    related_entity_id text null,
    payload text not null,
    processed_ok integer not null,
    error_text text null,
    created_at text not null default current_timestamp
);

create index if not exists idx_interface_message_control on interface_message_log(protocol, direction, message_type, control_id);

create table if not exists autoverification_rule (
    id text primary key,
    name text not null,
    active integer not null default 1,
    priority integer not null default 100,
    test_catalog_id text null references test_catalog(id),
    device_id text null references device(id),
    specimen_type_code text null,
    rule_type text not null check (rule_type in ('basic','delta')),
    condition_json text not null default '{}',
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists autoverification_run (
    id text primary key,
    observation_id text not null references observation(id) on delete cascade,
    rule_id text null references autoverification_rule(id),
    decision text not null check (decision in ('pass','fail','auto_finalized','held')),
    reasons_json text not null default '[]',
    evaluated_at text not null,
    created_task_id text null references task_work(id)
);

create index if not exists idx_autoverification_rule_scope on autoverification_rule(test_catalog_id, device_id, specimen_type_code, active);
create index if not exists idx_autoverification_run_observation on autoverification_run(observation_id, evaluated_at);
