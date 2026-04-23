-- v12 canonical PostgreSQL migration for analyzer runtime hardening.

alter table analyzer_transport_session add column if not exists lease_owner text null;
alter table analyzer_transport_session add column if not exists lease_acquired_at timestamptz null;
alter table analyzer_transport_session add column if not exists lease_expires_at timestamptz null;
alter table analyzer_transport_session add column if not exists heartbeat_at timestamptz null;
alter table analyzer_transport_session add column if not exists failure_count int not null default 0;
alter table analyzer_transport_session add column if not exists next_retry_at timestamptz null;

create index if not exists idx_transport_session_lease on analyzer_transport_session(lease_owner, lease_expires_at);
create index if not exists idx_transport_session_retry on analyzer_transport_session(next_retry_at, session_status);
