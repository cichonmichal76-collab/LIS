-- v12 canonical SQLite migration for analyzer runtime hardening.

alter table analyzer_transport_session add column lease_owner text null;
alter table analyzer_transport_session add column lease_acquired_at text null;
alter table analyzer_transport_session add column lease_expires_at text null;
alter table analyzer_transport_session add column heartbeat_at text null;
alter table analyzer_transport_session add column failure_count integer not null default 0;
alter table analyzer_transport_session add column next_retry_at text null;

create index if not exists idx_transport_session_lease on analyzer_transport_session(lease_owner, lease_expires_at);
create index if not exists idx_transport_session_retry on analyzer_transport_session(next_retry_at, session_status);
