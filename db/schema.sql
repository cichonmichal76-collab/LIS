-- Canonical target PostgreSQL schema for LIS v1.
-- This file captures the broader design target imported from the starter pack.
-- The currently implemented runtime slice still lives in db/migrations/0001_lis_core.sql.

create extension if not exists pgcrypto;

create table organization (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    type_code text null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table location (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid not null references organization(id),
    code text not null,
    name text not null,
    kind text not null,
    parent_location_id uuid null references location(id),
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (organization_id, code)
);

create table patient (
    id uuid primary key default gen_random_uuid(),
    mrn text not null unique,
    national_id text null,
    given_name text not null,
    family_name text not null,
    sex_code text null,
    birth_date date null,
    deceased boolean not null default false,
    merged_into_patient_id uuid null references patient(id),
    created_at timestamptz not null default now()
);

create table encounter_case (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references patient(id),
    encounter_no text null,
    case_no text null,
    status text not null,
    class_code text null,
    attending_org_id uuid null references organization(id),
    attending_location_id uuid null references location(id),
    started_at timestamptz null,
    ended_at timestamptz null,
    created_at timestamptz not null default now()
);

create table practitioner (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    given_name text not null,
    family_name text not null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table practitioner_role (
    id uuid primary key default gen_random_uuid(),
    practitioner_id uuid not null references practitioner(id),
    organization_id uuid not null references organization(id),
    role_code text not null,
    specialty_code text null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table app_user (
    id uuid primary key default gen_random_uuid(),
    username text not null unique,
    practitioner_role_id uuid null references practitioner_role(id),
    display_name text not null,
    is_system boolean not null default false,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table device (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    manufacturer text null,
    model text null,
    serial_no text null,
    protocol_code text null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table device_test_map (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id) on delete cascade,
    incoming_test_code text not null,
    test_catalog_id uuid not null references test_catalog(id),
    default_unit_ucum text null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique(device_id, incoming_test_code)
);

create index idx_device_test_map_device_code on device_test_map(device_id, incoming_test_code);

create table test_catalog (
    id uuid primary key default gen_random_uuid(),
    local_code text not null unique,
    display_name text not null,
    short_name text null,
    kind text not null check (kind in ('orderable','panel','analyte','aoe')),
    loinc_num text null,
    order_obs text null,
    specimen_type_code text null,
    method_code text null,
    default_ucum text null,
    result_value_type text not null check (result_value_type in ('quantity','text','coded','boolean','range','attachment')),
    active boolean not null default true,
    active_from date null,
    active_to date null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_test_catalog_loinc on test_catalog(loinc_num);

create table test_catalog_member (
    id uuid primary key default gen_random_uuid(),
    parent_test_catalog_id uuid not null references test_catalog(id) on delete cascade,
    child_test_catalog_id uuid not null references test_catalog(id),
    sort_order int not null,
    cardinality_min int not null default 0,
    cardinality_max int null,
    created_at timestamptz not null default now(),
    unique (parent_test_catalog_id, child_test_catalog_id)
);

create table qc_material (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    manufacturer text null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table qc_lot (
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

create index idx_qc_lot_scope on qc_lot(test_catalog_id, device_id, active);
create index idx_qc_lot_material on qc_lot(material_id, lot_no);

create table qc_rule (
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

create index idx_qc_rule_scope on qc_rule(test_catalog_id, device_id, active);

create table qc_run (
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

create index idx_qc_run_lot_status on qc_run(lot_id, status, created_at desc);
create index idx_qc_run_device_status on qc_run(device_id, status, created_at desc);

create table qc_result (
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

create index idx_qc_result_run on qc_result(run_id, created_at desc);
create index idx_qc_result_test_eval on qc_result(test_catalog_id, evaluated_at desc);

create table reference_interval (
    id uuid primary key default gen_random_uuid(),
    test_catalog_id uuid not null references test_catalog(id),
    sex_code text null,
    age_low_days int null,
    age_high_days int null,
    method_code text null,
    specimen_type_code text null,
    unit_ucum text null,
    low_num numeric null,
    high_num numeric null,
    text_range text null,
    critical_low_num numeric null,
    critical_high_num numeric null,
    active boolean not null default true,
    valid_from date null,
    valid_to date null,
    created_at timestamptz not null default now()
);

create table lis_order (
    id uuid primary key default gen_random_uuid(),
    requisition_no text not null unique,
    patient_id uuid not null references patient(id),
    encounter_case_id uuid null references encounter_case(id),
    source_system text not null,
    placer_order_no text null,
    filler_order_no text null,
    priority text not null check (priority in ('routine','urgent','asap','stat')),
    status text not null check (status in (
        'draft','registered','accepted','in_collection','received','in_process',
        'tech_review','med_review','released','amended','cancelled'
    )),
    clinical_info text null,
    requested_by_practitioner_role_id uuid null references practitioner_role(id),
    ordered_at timestamptz not null,
    received_at timestamptz null,
    cancelled_at timestamptz null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_lis_order_patient on lis_order(patient_id);
create index idx_lis_order_status on lis_order(status);
create index idx_lis_order_ordered_at on lis_order(ordered_at desc);

create table lis_order_item (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references lis_order(id) on delete cascade,
    line_no int not null,
    parent_item_id uuid null references lis_order_item(id),
    test_catalog_id uuid not null references test_catalog(id),
    requested_specimen_type_code text null,
    status text not null check (status in (
        'draft','registered','scheduled','collected','received','in_process',
        'tech_review','med_review','released','amended','cancelled','entered_in_error'
    )),
    priority text null check (priority in ('routine','urgent','asap','stat')),
    reflex_policy_code text null,
    aoe_payload jsonb not null default '{}'::jsonb,
    external_fhir_id text null,
    created_at timestamptz not null default now(),
    unique(order_id, line_no)
);

create index idx_lis_order_item_order on lis_order_item(order_id);
create index idx_lis_order_item_status on lis_order_item(status);

create table specimen (
    id uuid primary key default gen_random_uuid(),
    accession_no text not null unique,
    order_id uuid not null references lis_order(id),
    patient_id uuid not null references patient(id),
    parent_specimen_id uuid null references specimen(id),
    specimen_type_code text not null,
    status text not null check (status in (
        'expected','collected','received','accepted','aliquoted','in_process','stored','rejected','disposed'
    )),
    collected_at timestamptz null,
    collected_by_practitioner_role_id uuid null references practitioner_role(id),
    collection_site_code text null,
    received_at timestamptz null,
    accepted_at timestamptz null,
    rejected_at timestamptz null,
    rejection_reason_code text null,
    source_location_id uuid null references location(id),
    notes text null,
    created_at timestamptz not null default now()
);

create index idx_specimen_order on specimen(order_id);
create index idx_specimen_patient on specimen(patient_id);
create index idx_specimen_status on specimen(status);

create table storage_location (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    kind text not null,
    parent_storage_location_id uuid null references storage_location(id),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table container (
    id uuid primary key default gen_random_uuid(),
    specimen_id uuid not null references specimen(id) on delete cascade,
    parent_container_id uuid null references container(id),
    barcode text not null unique,
    container_type_code text not null,
    position_code text null,
    volume_value numeric null,
    volume_ucum text null,
    storage_location_id uuid null references storage_location(id),
    status text not null check (status in ('created','labeled','filled','in_transit','stored','disposed')),
    created_at timestamptz not null default now()
);

create index idx_container_specimen on container(specimen_id);

create table specimen_event (
    id uuid primary key default gen_random_uuid(),
    specimen_id uuid not null references specimen(id) on delete cascade,
    container_id uuid null references container(id),
    event_type text not null,
    event_at timestamptz not null,
    actor_user_id uuid null references app_user(id),
    actor_device_id uuid null references device(id),
    location_id uuid null references location(id),
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_specimen_event_specimen on specimen_event(specimen_id, event_at desc);

create table task_work (
    id uuid primary key default gen_random_uuid(),
    group_identifier text null,
    based_on_order_item_id uuid null references lis_order_item(id),
    focus_type text not null,
    focus_id uuid not null,
    queue_code text not null,
    status text not null check (status in ('created','ready','in_progress','on_hold','completed','failed','cancelled')),
    business_status text null,
    owner_user_id uuid null references app_user(id),
    owner_role_id uuid null references practitioner_role(id),
    device_id uuid null references device(id),
    authored_on timestamptz not null,
    ready_at timestamptz null,
    started_at timestamptz null,
    completed_at timestamptz null,
    failed_reason text null,
    inputs jsonb not null default '{}'::jsonb,
    outputs jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_task_work_queue_status on task_work(queue_code, status);
create index idx_task_work_focus on task_work(focus_type, focus_id);

create table raw_instrument_message (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id),
    work_task_id uuid null references task_work(id),
    protocol text not null,
    direction text not null check (direction in ('inbound','outbound')),
    parser_version text not null,
    checksum text null,
    accession_no text null,
    specimen_barcode text null,
    received_at timestamptz not null,
    payload text not null,
    parsed_ok boolean not null,
    parse_error text null,
    created_at timestamptz not null default now()
);

create index idx_raw_msg_device_received on raw_instrument_message(device_id, received_at desc);
create index idx_raw_msg_accession on raw_instrument_message(accession_no);

create table interface_message_log (
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

create index idx_interface_message_control on interface_message_log(protocol, direction, message_type, control_id);

create table observation (
    id uuid primary key default gen_random_uuid(),
    order_item_id uuid not null references lis_order_item(id),
    specimen_id uuid null references specimen(id),
    code_local text not null,
    code_loinc text null,
    status text not null check (status in ('registered','preliminary','final','amended','corrected','cancelled','entered_in_error')),
    category_code text not null default 'laboratory',
    value_type text not null check (value_type in ('quantity','text','coded','boolean','range','attachment')),
    value_num numeric null,
    value_text text null,
    value_boolean boolean null,
    value_code_system text null,
    value_code text null,
    unit_ucum text null,
    comparator text null,
    interpretation_code text null,
    abnormal_flag text null,
    method_code text null,
    performer_practitioner_role_id uuid null references practitioner_role(id),
    device_id uuid null references device(id),
    raw_message_id uuid null references raw_instrument_message(id),
    effective_at timestamptz null,
    issued_at timestamptz null,
    reference_interval_snapshot jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_observation_order_item on observation(order_item_id);
create index idx_observation_specimen on observation(specimen_id);
create index idx_observation_status on observation(status);
create index idx_observation_code_loinc on observation(code_loinc);

create table observation_link (
    id uuid primary key default gen_random_uuid(),
    source_observation_id uuid not null references observation(id) on delete cascade,
    target_observation_id uuid not null references observation(id) on delete cascade,
    relation_type text not null check (relation_type in ('has_member','derived_from','triggered_by','replaces','sequel_to')),
    created_at timestamptz not null default now(),
    unique(source_observation_id, target_observation_id, relation_type)
);

create table autoverification_rule (
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

create table autoverification_run (
    id uuid primary key default gen_random_uuid(),
    observation_id uuid not null references observation(id) on delete cascade,
    rule_id uuid null references autoverification_rule(id),
    decision text not null check (decision in ('pass','fail','auto_finalized','held')),
    reasons_json jsonb not null default '[]'::jsonb,
    evaluated_at timestamptz not null,
    created_task_id uuid null references task_work(id)
);

create index idx_autoverification_rule_scope on autoverification_rule(test_catalog_id, device_id, specimen_type_code, active);
create index idx_autoverification_run_observation on autoverification_run(observation_id, evaluated_at desc);

create table analyzer_transport_profile (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id) on delete cascade,
    protocol text not null check (protocol in ('astm-transport')),
    framing_mode text not null check (framing_mode in ('astm-e1381')),
    connection_mode text not null default 'mock' check (connection_mode in ('mock','tcp-client','serial')),
    tcp_host text null,
    tcp_port int null,
    serial_port text null,
    serial_baudrate int null,
    frame_payload_size int not null,
    ack_timeout_seconds int not null,
    max_retries int not null,
    poll_interval_seconds int not null default 1,
    read_timeout_seconds int not null default 1,
    write_timeout_seconds int not null default 5,
    auto_dispatch_astm boolean not null default true,
    auto_verify boolean not null default false,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table analyzer_transport_session (
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

create table analyzer_transport_message (
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

create table analyzer_transport_frame_log (
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

create index idx_transport_profile_device on analyzer_transport_profile(device_id, active);
create index idx_transport_session_device on analyzer_transport_session(device_id, created_at);
create index idx_transport_message_session on analyzer_transport_message(session_id, direction, transport_status, created_at);
create index idx_transport_frame_session on analyzer_transport_frame_log(session_id, created_at);
create index idx_transport_frame_message on analyzer_transport_frame_log(message_id, created_at);

create table diagnostic_report (
    id uuid primary key default gen_random_uuid(),
    report_no text not null unique,
    order_id uuid not null references lis_order(id),
    patient_id uuid not null references patient(id),
    status text not null check (status in ('registered','partial','preliminary','final','amended','corrected','entered_in_error')),
    category_code text not null default 'laboratory',
    code_local text null,
    code_loinc text null,
    effective_at timestamptz null,
    issued_at timestamptz null,
    interpreter_practitioner_role_id uuid null references practitioner_role(id),
    conclusion_text text null,
    current_version_no int not null default 1,
    created_at timestamptz not null default now()
);

create index idx_diagnostic_report_order on diagnostic_report(order_id);
create index idx_diagnostic_report_patient on diagnostic_report(patient_id);

create table diagnostic_report_version (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references diagnostic_report(id) on delete cascade,
    version_no int not null,
    status text not null,
    amendment_reason text null,
    rendered_pdf_uri text null,
    signed_by_user_id uuid null references app_user(id),
    signed_at timestamptz null,
    payload jsonb not null,
    created_at timestamptz not null default now(),
    unique(report_id, version_no)
);

create table report_observation (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references diagnostic_report(id) on delete cascade,
    observation_id uuid not null references observation(id),
    sort_order int not null default 0,
    created_at timestamptz not null default now(),
    unique(report_id, observation_id)
);

create table audit_event_log (
    id uuid primary key default gen_random_uuid(),
    occurred_at timestamptz not null,
    actor_user_id uuid null references app_user(id),
    actor_device_id uuid null references device(id),
    actor_ip inet null,
    action_code text not null,
    entity_type text not null,
    entity_id uuid null,
    entity_identifier text null,
    outcome_code text null,
    reason_code text null,
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_audit_entity on audit_event_log(entity_type, entity_id, occurred_at desc);
create index idx_audit_actor on audit_event_log(actor_user_id, occurred_at desc);

create table provenance_record (
    id uuid primary key default gen_random_uuid(),
    target_type text not null,
    target_id uuid not null,
    activity_code text not null,
    recorded_at timestamptz not null,
    agent_user_id uuid null references app_user(id),
    agent_device_id uuid null references device(id),
    based_on_type text null,
    based_on_id uuid null,
    signature_type text null,
    signature_value text null,
    details jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index idx_provenance_target on provenance_record(target_type, target_id, recorded_at desc);
