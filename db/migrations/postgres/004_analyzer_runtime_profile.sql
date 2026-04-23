-- v9 canonical PostgreSQL migration for analyzer runtime endpoint configuration.

alter table analyzer_transport_profile
    add column if not exists connection_mode text not null default 'mock',
    add column if not exists tcp_host text null,
    add column if not exists tcp_port int null,
    add column if not exists serial_port text null,
    add column if not exists serial_baudrate int null,
    add column if not exists poll_interval_seconds int not null default 1,
    add column if not exists read_timeout_seconds int not null default 1,
    add column if not exists write_timeout_seconds int not null default 5,
    add column if not exists auto_dispatch_astm boolean not null default true,
    add column if not exists auto_verify boolean not null default false;

alter table analyzer_transport_profile
    drop constraint if exists analyzer_transport_profile_connection_mode_check;

alter table analyzer_transport_profile
    add constraint analyzer_transport_profile_connection_mode_check
    check (connection_mode in ('mock','tcp-client','serial'));
