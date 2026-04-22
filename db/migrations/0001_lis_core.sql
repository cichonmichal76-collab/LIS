create extension if not exists pgcrypto;

create table organization (
    id uuid primary key default gen_random_uuid(),
    code text unique,
    name text not null,
    kind text not null default 'provider',
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table location (
    id uuid primary key default gen_random_uuid(),
    organization_id uuid null references organization(id),
    code text unique,
    name text not null,
    kind text not null default 'site',
    parent_location_id uuid null references location(id),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table patient (
    id uuid primary key default gen_random_uuid(),
    mrn text not null unique,
    external_id text null,
    first_name text not null,
    last_name text not null,
    birth_date date null,
    sex_code text null,
    phone text null,
    email text null,
    active boolean not null default true,
    merged_into_patient_id uuid null references patient(id),
    created_at timestamptz not null default now()
);

create table encounter_case (
    id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references patient(id),
    organization_id uuid null references organization(id),
    location_id uuid null references location(id),
    case_no text null unique,
    external_case_id text null,
    status text not null default 'active',
    attending_practitioner_id uuid null,
    opened_at timestamptz not null default now(),
    closed_at timestamptz null
);

create table practitioner (
    id uuid primary key default gen_random_uuid(),
    external_id text null unique,
    first_name text not null,
    last_name text not null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table practitioner_role (
    id uuid primary key default gen_random_uuid(),
    practitioner_id uuid not null references practitioner(id),
    organization_id uuid null references organization(id),
    location_id uuid null references location(id),
    role_code text not null,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

alter table encounter_case
    add constraint fk_encounter_case_attending_practitioner
    foreign key (attending_practitioner_id) references practitioner(id);

create table app_user (
    id uuid primary key default gen_random_uuid(),
    username text not null unique,
    display_name text not null,
    practitioner_role_id uuid null references practitioner_role(id),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table device (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    display_name text not null,
    manufacturer text null,
    model text null,
    serial_number text null,
    organization_id uuid null references organization(id),
    location_id uuid null references location(id),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table test_catalog (
    id uuid primary key default gen_random_uuid(),
    local_code text not null unique,
    display_name text not null,
    kind text not null check (kind in ('orderable', 'panel', 'analyte', 'aoe')),
    loinc_num text null,
    order_obs text null,
    default_ucum text null,
    specimen_type_code text null,
    method_code text null,
    panel_type text null,
    common_order_rank integer null,
    common_test_rank integer null,
    example_ucum_units text null,
    replaces_local_code text null,
    active_from timestamptz not null default now(),
    active_to timestamptz null,
    metadata jsonb not null default '{}'::jsonb
);

create table test_catalog_member (
    id uuid primary key default gen_random_uuid(),
    parent_test_catalog_id uuid not null references test_catalog(id),
    member_test_catalog_id uuid not null references test_catalog(id),
    relation_type text not null default 'has-member',
    sort_order integer not null default 1,
    min_occurs integer not null default 0,
    max_occurs integer null,
    unique (parent_test_catalog_id, member_test_catalog_id, relation_type)
);

create table reference_interval (
    id uuid primary key default gen_random_uuid(),
    test_catalog_id uuid not null references test_catalog(id),
    sex_code text null,
    age_low numeric null,
    age_high numeric null,
    age_ucum text null default 'a',
    lower_bound_num numeric null,
    upper_bound_num numeric null,
    unit_ucum text null,
    interpretation_text text null,
    active_from timestamptz not null default now(),
    active_to timestamptz null
);

create table lis_order (
    id uuid primary key default gen_random_uuid(),
    requisition_no text not null unique,
    patient_id uuid not null references patient(id),
    encounter_case_id uuid null references encounter_case(id),
    source_system text not null,
    placer_order_no text null,
    filler_order_no text null,
    priority text not null check (priority in ('routine', 'urgent', 'asap', 'stat')),
    status text not null,
    clinical_info text null,
    requested_by_practitioner_role_id uuid null references practitioner_role(id),
    ordered_at timestamptz not null,
    received_at timestamptz null,
    cancelled_at timestamptz null,
    metadata jsonb not null default '{}'::jsonb
);

create table lis_order_item (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references lis_order(id),
    line_no integer not null,
    parent_item_id uuid null references lis_order_item(id),
    test_catalog_id uuid not null references test_catalog(id),
    requested_specimen_type_code text null,
    status text not null,
    priority text null,
    fhir_service_request_id text null,
    aoe_payload jsonb not null default '{}'::jsonb,
    reflex_policy_code text null,
    performing_location_id uuid null references location(id),
    requested_at timestamptz not null default now(),
    cancelled_at timestamptz null,
    unique (order_id, line_no)
);

create table specimen (
    id uuid primary key default gen_random_uuid(),
    accession_no text not null unique,
    order_id uuid not null references lis_order(id),
    parent_specimen_id uuid null references specimen(id),
    patient_id uuid not null references patient(id),
    specimen_type_code text not null,
    status text not null,
    collected_at timestamptz null,
    collected_by_practitioner_role_id uuid null references practitioner_role(id),
    received_at timestamptz null,
    accepted_at timestamptz null,
    rejected_at timestamptz null,
    rejection_reason_code text null,
    source_location_id uuid null references location(id),
    notes text null,
    metadata jsonb not null default '{}'::jsonb
);

create table container (
    id uuid primary key default gen_random_uuid(),
    specimen_id uuid not null references specimen(id),
    parent_container_id uuid null references container(id),
    barcode text not null unique,
    container_type_code text not null,
    label text null,
    position_code text null,
    volume_value numeric null,
    volume_ucum text null,
    storage_location_id uuid null references location(id),
    status text not null,
    created_at timestamptz not null default now()
);

create table specimen_event (
    id uuid primary key default gen_random_uuid(),
    specimen_id uuid not null references specimen(id),
    event_type text not null,
    performed_by_user_id uuid null references app_user(id),
    location_id uuid null references location(id),
    occurred_at timestamptz not null default now(),
    details jsonb not null default '{}'::jsonb
);

create table task_work (
    id uuid primary key default gen_random_uuid(),
    group_identifier text null,
    based_on_order_item_id uuid null references lis_order_item(id),
    focus_type text not null check (focus_type in ('order-item', 'specimen', 'observation', 'report')),
    focus_id uuid not null,
    queue_code text not null,
    status text not null,
    business_status text null,
    owner_user_id uuid null references app_user(id),
    owner_practitioner_role_id uuid null references practitioner_role(id),
    device_id uuid null references device(id),
    priority text null,
    authored_on timestamptz not null default now(),
    ready_at timestamptz null,
    started_at timestamptz null,
    completed_at timestamptz null,
    due_at timestamptz null,
    failed_reason text null,
    inputs jsonb not null default '{}'::jsonb,
    outputs jsonb not null default '{}'::jsonb
);

create table raw_instrument_message (
    id uuid primary key default gen_random_uuid(),
    device_id uuid not null references device(id),
    work_task_id uuid null references task_work(id),
    protocol text not null,
    direction text not null check (direction in ('inbound', 'outbound')),
    parser_version text not null,
    checksum text null,
    accession_no text null,
    specimen_barcode text null,
    correlation_id text null,
    received_at timestamptz not null default now(),
    payload text not null,
    parsed_ok boolean not null,
    parse_error text null
);

create table observation (
    id uuid primary key default gen_random_uuid(),
    order_item_id uuid not null references lis_order_item(id),
    specimen_id uuid null references specimen(id),
    code_local text not null,
    code_loinc text null,
    status text not null,
    category_code text not null default 'laboratory',
    value_type text not null check (value_type in ('quantity', 'text', 'coded', 'boolean', 'range', 'attachment')),
    value_num numeric null,
    value_text text null,
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
    metadata jsonb not null default '{}'::jsonb
);

create table observation_link (
    id uuid primary key default gen_random_uuid(),
    source_observation_id uuid not null references observation(id),
    target_observation_id uuid not null references observation(id),
    relation_type text not null check (relation_type in ('has-member', 'derived-from', 'triggered-by', 'replaces', 'sequel-to')),
    unique (source_observation_id, target_observation_id, relation_type)
);

create table diagnostic_report (
    id uuid primary key default gen_random_uuid(),
    report_no text not null unique,
    order_id uuid not null references lis_order(id),
    patient_id uuid not null references patient(id),
    status text not null,
    category_code text not null default 'laboratory',
    code_local text null,
    code_loinc text null,
    effective_at timestamptz null,
    issued_at timestamptz null,
    interpreter_practitioner_role_id uuid null references practitioner_role(id),
    conclusion_text text null,
    published_channel text null,
    current_version_no integer not null default 1
);

create table diagnostic_report_version (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references diagnostic_report(id),
    version_no integer not null,
    status text not null,
    amendment_reason text null,
    rendered_pdf_uri text null,
    signed_by_user_id uuid null references app_user(id),
    signed_at timestamptz null,
    payload jsonb not null,
    unique (report_id, version_no)
);

create table report_observation (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references diagnostic_report(id),
    observation_id uuid not null references observation(id),
    sort_order integer not null default 1,
    unique (report_id, observation_id)
);

create table audit_event_log (
    id uuid primary key default gen_random_uuid(),
    entity_type text not null,
    entity_id uuid not null,
    action text not null,
    status text not null,
    actor_user_id uuid null references app_user(id),
    actor_practitioner_role_id uuid null references practitioner_role(id),
    source_system text null,
    source_ip text null,
    request_id text null,
    event_at timestamptz not null default now(),
    diff jsonb not null default '{}'::jsonb,
    context jsonb not null default '{}'::jsonb
);

create table provenance_record (
    id uuid primary key default gen_random_uuid(),
    target_resource_type text not null,
    target_resource_id uuid not null,
    activity_code text not null,
    based_on_order_id uuid null references lis_order(id),
    based_on_order_item_id uuid null references lis_order_item(id),
    specimen_id uuid null references specimen(id),
    observation_id uuid null references observation(id),
    report_version_id uuid null references diagnostic_report_version(id),
    device_id uuid null references device(id),
    agent_user_id uuid null references app_user(id),
    agent_practitioner_role_id uuid null references practitioner_role(id),
    recorded_at timestamptz not null default now(),
    inputs jsonb not null default '{}'::jsonb,
    signature jsonb not null default '{}'::jsonb
);

create index idx_encounter_case_patient on encounter_case(patient_id);
create index idx_practitioner_role_practitioner on practitioner_role(practitioner_id);
create index idx_device_location on device(location_id);
create index idx_test_catalog_loinc on test_catalog(loinc_num);
create index idx_reference_interval_test on reference_interval(test_catalog_id);

create index idx_lis_order_patient_status on lis_order(patient_id, status);
create index idx_lis_order_requested_by on lis_order(requested_by_practitioner_role_id);
create index idx_lis_order_item_order_status on lis_order_item(order_id, status);
create index idx_lis_order_item_test on lis_order_item(test_catalog_id);

create index idx_specimen_order_status on specimen(order_id, status);
create index idx_specimen_patient on specimen(patient_id);
create index idx_container_specimen on container(specimen_id);
create index idx_specimen_event_specimen on specimen_event(specimen_id, occurred_at desc);

create index idx_task_work_queue_status on task_work(queue_code, status);
create index idx_task_work_owner on task_work(owner_user_id, status);
create index idx_task_work_focus on task_work(focus_type, focus_id);
create index idx_raw_instrument_message_device_received on raw_instrument_message(device_id, received_at desc);
create index idx_raw_instrument_message_accession on raw_instrument_message(accession_no);

create index idx_observation_order_item_status on observation(order_item_id, status);
create index idx_observation_specimen on observation(specimen_id);
create index idx_observation_code_loinc on observation(code_loinc);
create index idx_observation_link_source on observation_link(source_observation_id);

create index idx_diagnostic_report_order on diagnostic_report(order_id, status);
create index idx_diagnostic_report_patient on diagnostic_report(patient_id, issued_at desc);
create index idx_diagnostic_report_version_report on diagnostic_report_version(report_id, version_no desc);
create index idx_report_observation_report on report_observation(report_id, sort_order);

create index idx_audit_event_entity on audit_event_log(entity_type, entity_id, event_at desc);
create index idx_audit_event_request on audit_event_log(request_id);
create index idx_provenance_target on provenance_record(target_resource_type, target_resource_id, recorded_at desc);
create index idx_provenance_order on provenance_record(based_on_order_id);
