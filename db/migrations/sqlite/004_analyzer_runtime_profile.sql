-- v9 canonical SQLite migration for analyzer runtime endpoint configuration.

alter table analyzer_transport_profile add column connection_mode text not null default 'mock'
    check (connection_mode in ('mock','tcp-client','serial'));
alter table analyzer_transport_profile add column tcp_host text null;
alter table analyzer_transport_profile add column tcp_port integer null;
alter table analyzer_transport_profile add column serial_port text null;
alter table analyzer_transport_profile add column serial_baudrate integer null;
alter table analyzer_transport_profile add column poll_interval_seconds integer not null default 1;
alter table analyzer_transport_profile add column read_timeout_seconds integer not null default 1;
alter table analyzer_transport_profile add column write_timeout_seconds integer not null default 5;
alter table analyzer_transport_profile add column auto_dispatch_astm integer not null default 1;
alter table analyzer_transport_profile add column auto_verify integer not null default 0;
