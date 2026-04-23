-- v8 canonical SQLite migration for analyzer transport sessions,
-- framed ASTM-style transport, and frame/event logs.

create table if not exists analyzer_transport_profile (
    id text primary key,
    device_id text not null references device(id) on delete cascade,
    protocol text not null check (protocol in ('astm-transport')),
    framing_mode text not null check (framing_mode in ('astm-e1381')),
    frame_payload_size integer not null,
    ack_timeout_seconds integer not null,
    max_retries integer not null,
    active integer not null default 1,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists analyzer_transport_session (
    id text primary key,
    device_id text not null references device(id) on delete cascade,
    profile_id text not null references analyzer_transport_profile(id),
    session_status text not null check (
        session_status in ('idle','sending','receiving','awaiting_ack','closed','error')
    ),
    outbound_message_id text null,
    inbound_message_id text null,
    expected_inbound_frame_no integer not null default 1,
    last_error text null,
    last_activity_at text not null default current_timestamp,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    closed_at text null
);

create table if not exists analyzer_transport_message (
    id text primary key,
    session_id text not null references analyzer_transport_session(id) on delete cascade,
    device_id text not null references device(id) on delete cascade,
    direction text not null check (direction in ('inbound','outbound')),
    protocol text not null,
    message_type text not null,
    transport_status text not null check (
        transport_status in ('queued','ready','awaiting_ack','resend','completed','failed','receiving','received','dispatched')
    ),
    logical_payload text not null,
    assembled_payload text null,
    frames_json text not null default '[]',
    total_frames integer not null default 0,
    next_frame_index integer not null default 0,
    pending_frame_index integer null,
    last_sent_kind text null check (last_sent_kind in ('ENQ','FRAME','EOT')),
    retry_count integer not null default 0,
    correlation_key text null,
    ack_deadline_at text null,
    parse_error text null,
    dispatched_entity_type text null,
    dispatched_entity_id text null,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    completed_at text null
);

create table if not exists analyzer_transport_frame_log (
    id text primary key,
    session_id text not null references analyzer_transport_session(id) on delete cascade,
    message_id text null references analyzer_transport_message(id) on delete cascade,
    direction text not null check (direction in ('inbound','outbound')),
    event_kind text not null check (event_kind in ('control','frame')),
    control_code text null,
    frame_no integer null,
    payload_chunk text null,
    framed_payload text null,
    checksum_hex text null,
    is_final integer null,
    accepted integer not null default 1,
    duplicate_flag integer not null default 0,
    retry_no integer not null default 0,
    notes text null,
    created_at text not null default current_timestamp
);

create index if not exists idx_transport_profile_device on analyzer_transport_profile(device_id, active);
create index if not exists idx_transport_session_device on analyzer_transport_session(device_id, created_at);
create index if not exists idx_transport_message_session on analyzer_transport_message(session_id, direction, transport_status, created_at);
create index if not exists idx_transport_frame_session on analyzer_transport_frame_log(session_id, created_at);
create index if not exists idx_transport_frame_message on analyzer_transport_frame_log(message_id, created_at);
