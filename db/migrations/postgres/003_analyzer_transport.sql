-- v8 canonical PostgreSQL migration for analyzer transport sessions,
-- framed ASTM-style transport, and frame/event logs.

create table if not exists analyzer_transport_profile (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id) on delete cascade,
    protocol text not null check (protocol in ('astm-transport')),
    framing_mode text not null check (framing_mode in ('astm-e1381')),
    frame_payload_size int not null,
    ack_timeout_seconds int not null,
    max_retries int not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists analyzer_transport_session (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id) on delete cascade,
    profile_id uuid not null references analyzer_transport_profile(id),
    session_status text not null check (
        session_status in ('idle','sending','receiving','awaiting_ack','closed','error')
    ),
    outbound_message_id uuid null,
    inbound_message_id uuid null,
    expected_inbound_frame_no int not null default 1,
    last_error text null,
    last_activity_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    closed_at timestamptz null
);

create table if not exists analyzer_transport_message (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references analyzer_transport_session(id) on delete cascade,
    device_id uuid not null references device(id) on delete cascade,
    direction text not null check (direction in ('inbound','outbound')),
    protocol text not null,
    message_type text not null,
    transport_status text not null check (
        transport_status in ('queued','ready','awaiting_ack','resend','completed','failed','receiving','received','dispatched')
    ),
    logical_payload text not null,
    assembled_payload text null,
    frames_json jsonb not null default '[]'::jsonb,
    total_frames int not null default 0,
    next_frame_index int not null default 0,
    pending_frame_index int null,
    last_sent_kind text null check (last_sent_kind in ('ENQ','FRAME','EOT')),
    retry_count int not null default 0,
    correlation_key text null,
    ack_deadline_at timestamptz null,
    parse_error text null,
    dispatched_entity_type text null,
    dispatched_entity_id uuid null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    completed_at timestamptz null
);

create table if not exists analyzer_transport_frame_log (
    id uuid primary key default gen_random_uuid(),
    session_id uuid not null references analyzer_transport_session(id) on delete cascade,
    message_id uuid null references analyzer_transport_message(id) on delete cascade,
    direction text not null check (direction in ('inbound','outbound')),
    event_kind text not null check (event_kind in ('control','frame')),
    control_code text null,
    frame_no int null,
    payload_chunk text null,
    framed_payload text null,
    checksum_hex text null,
    is_final boolean null,
    accepted boolean not null default true,
    duplicate_flag boolean not null default false,
    retry_no int not null default 0,
    notes text null,
    created_at timestamptz not null default now()
);

create index if not exists idx_transport_profile_device on analyzer_transport_profile(device_id, active);
create index if not exists idx_transport_session_device on analyzer_transport_session(device_id, created_at);
create index if not exists idx_transport_message_session on analyzer_transport_message(session_id, direction, transport_status, created_at);
create index if not exists idx_transport_frame_session on analyzer_transport_frame_log(session_id, created_at);
create index if not exists idx_transport_frame_message on analyzer_transport_frame_log(message_id, created_at);
