-- Generated runtime bootstrap for sqlite.
-- Source of truth: app/db/models.py

CREATE TABLE IF NOT EXISTS app_user_runtime (
	id VARCHAR(36) NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	display_name VARCHAR(128) NOT NULL, 
	role_code VARCHAR(32) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);
CREATE INDEX IF NOT EXISTS ix_app_user_runtime_role_active ON app_user_runtime (role_code, active);
CREATE INDEX IF NOT EXISTS ix_app_user_runtime_username ON app_user_runtime (username);

CREATE TABLE IF NOT EXISTS audit_event_log_runtime (
	id VARCHAR(36) NOT NULL, 
	entity_type VARCHAR(64) NOT NULL, 
	entity_id VARCHAR(36) NOT NULL, 
	action VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	source_system VARCHAR(64), 
	event_at DATETIME NOT NULL, 
	context JSON NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_audit_event_log_runtime_entity ON audit_event_log_runtime (entity_type, entity_id, event_at);

CREATE TABLE IF NOT EXISTS device_runtime (
	id VARCHAR(36) NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	manufacturer VARCHAR(128), 
	model VARCHAR(128), 
	serial_no VARCHAR(128), 
	protocol_code VARCHAR(64), 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);
CREATE INDEX IF NOT EXISTS ix_device_runtime_code ON device_runtime (code);
CREATE INDEX IF NOT EXISTS ix_device_runtime_protocol_active ON device_runtime (protocol_code, active);

CREATE TABLE IF NOT EXISTS interface_message_log_runtime (
	id VARCHAR(36) NOT NULL, 
	protocol VARCHAR(32) NOT NULL, 
	direction VARCHAR(16) NOT NULL, 
	message_type VARCHAR(64) NOT NULL, 
	control_id VARCHAR(128), 
	related_entity_type VARCHAR(64), 
	related_entity_id VARCHAR(36), 
	payload TEXT NOT NULL, 
	processed_ok BOOLEAN NOT NULL, 
	error_text TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_interface_message_log_runtime_control_id ON interface_message_log_runtime (control_id);
CREATE INDEX IF NOT EXISTS ix_interface_message_log_runtime_protocol_created ON interface_message_log_runtime (protocol, created_at);

CREATE TABLE IF NOT EXISTS patient_runtime (
	id VARCHAR(36) NOT NULL, 
	mrn VARCHAR(64) NOT NULL, 
	given_name VARCHAR(128) NOT NULL, 
	family_name VARCHAR(128) NOT NULL, 
	sex_code VARCHAR(16), 
	birth_date DATE, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (mrn)
);
CREATE INDEX IF NOT EXISTS ix_patient_runtime_family_name ON patient_runtime (family_name);
CREATE INDEX IF NOT EXISTS ix_patient_runtime_mrn ON patient_runtime (mrn);

CREATE TABLE IF NOT EXISTS provenance_record_runtime (
	id VARCHAR(36) NOT NULL, 
	target_resource_type VARCHAR(64) NOT NULL, 
	target_resource_id VARCHAR(36) NOT NULL, 
	activity_code VARCHAR(64) NOT NULL, 
	based_on_order_id VARCHAR(36), 
	based_on_order_item_id VARCHAR(36), 
	specimen_id VARCHAR(36), 
	observation_id VARCHAR(36), 
	report_version_id VARCHAR(36), 
	device_id VARCHAR(36), 
	agent_user_id VARCHAR(36), 
	agent_practitioner_role_id VARCHAR(36), 
	recorded_at DATETIME NOT NULL, 
	inputs JSON NOT NULL, 
	signature JSON NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX IF NOT EXISTS ix_provenance_record_runtime_target ON provenance_record_runtime (target_resource_type, target_resource_id, recorded_at);

CREATE TABLE IF NOT EXISTS qc_material_runtime (
	id VARCHAR(36) NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	manufacturer VARCHAR(128), 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);
CREATE INDEX IF NOT EXISTS ix_qc_material_runtime_code ON qc_material_runtime (code);

CREATE TABLE IF NOT EXISTS test_catalog_runtime (
	id VARCHAR(36) NOT NULL, 
	local_code VARCHAR(64) NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	kind VARCHAR(32) NOT NULL, 
	loinc_num VARCHAR(64), 
	specimen_type_code VARCHAR(64), 
	default_ucum VARCHAR(32), 
	result_value_type VARCHAR(32) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (local_code)
);
CREATE INDEX IF NOT EXISTS ix_test_catalog_runtime_local_code ON test_catalog_runtime (local_code);
CREATE INDEX IF NOT EXISTS ix_test_catalog_runtime_loinc ON test_catalog_runtime (loinc_num);

CREATE TABLE IF NOT EXISTS analyzer_transport_profile_runtime (
	id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	protocol VARCHAR(32) NOT NULL, 
	framing_mode VARCHAR(32) NOT NULL, 
	connection_mode VARCHAR(32) NOT NULL, 
	tcp_host VARCHAR(255), 
	tcp_port INTEGER, 
	serial_port VARCHAR(255), 
	serial_baudrate INTEGER, 
	frame_payload_size INTEGER NOT NULL, 
	ack_timeout_seconds INTEGER NOT NULL, 
	max_retries INTEGER NOT NULL, 
	poll_interval_seconds INTEGER NOT NULL, 
	read_timeout_seconds INTEGER NOT NULL, 
	write_timeout_seconds INTEGER NOT NULL, 
	auto_dispatch_astm BOOLEAN NOT NULL, 
	auto_verify BOOLEAN NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_transport_profile_runtime_device_active ON analyzer_transport_profile_runtime (device_id, active);

CREATE TABLE IF NOT EXISTS autoverification_rule_runtime (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	active BOOLEAN NOT NULL, 
	priority INTEGER NOT NULL, 
	test_catalog_id VARCHAR(36), 
	device_id VARCHAR(36), 
	specimen_type_code VARCHAR(64), 
	rule_type VARCHAR(32) NOT NULL, 
	condition_json JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_autoverification_rule_runtime_scope ON autoverification_rule_runtime (test_catalog_id, device_id, specimen_type_code, active);

CREATE TABLE IF NOT EXISTS device_test_map_runtime (
	id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	incoming_test_code VARCHAR(128) NOT NULL, 
	test_catalog_id VARCHAR(36) NOT NULL, 
	default_unit_ucum VARCHAR(32), 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_device_test_map_runtime_device_code ON device_test_map_runtime (device_id, incoming_test_code);

CREATE TABLE IF NOT EXISTS lis_order_runtime (
	id VARCHAR(36) NOT NULL, 
	requisition_no VARCHAR(64) NOT NULL, 
	patient_id VARCHAR(36) NOT NULL, 
	encounter_case_id VARCHAR(36), 
	source_system VARCHAR(64) NOT NULL, 
	placer_order_no VARCHAR(128), 
	priority VARCHAR(24) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	clinical_info TEXT, 
	requested_by_practitioner_role_id VARCHAR(36), 
	ordered_at DATETIME NOT NULL, 
	received_at DATETIME, 
	cancelled_at DATETIME, 
	metadata JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (requisition_no), 
	FOREIGN KEY(patient_id) REFERENCES patient_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_lis_order_runtime_patient_id ON lis_order_runtime (patient_id);
CREATE INDEX IF NOT EXISTS ix_lis_order_runtime_patient_status ON lis_order_runtime (patient_id, status);
CREATE INDEX IF NOT EXISTS ix_lis_order_runtime_requisition ON lis_order_runtime (requisition_no);

CREATE TABLE IF NOT EXISTS qc_lot_runtime (
	id VARCHAR(36) NOT NULL, 
	material_id VARCHAR(36) NOT NULL, 
	lot_no VARCHAR(64) NOT NULL, 
	test_catalog_id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36), 
	unit_ucum VARCHAR(32), 
	target_mean FLOAT, 
	target_sd FLOAT, 
	min_value FLOAT, 
	max_value FLOAT, 
	active BOOLEAN NOT NULL, 
	expires_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(material_id) REFERENCES qc_material_runtime (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_qc_lot_runtime_material_lot ON qc_lot_runtime (material_id, lot_no);
CREATE INDEX IF NOT EXISTS ix_qc_lot_runtime_test_device ON qc_lot_runtime (test_catalog_id, device_id, active);

CREATE TABLE IF NOT EXISTS qc_rule_runtime (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	active BOOLEAN NOT NULL, 
	priority INTEGER NOT NULL, 
	test_catalog_id VARCHAR(36), 
	device_id VARCHAR(36), 
	rule_type VARCHAR(32) NOT NULL, 
	params_json JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_qc_rule_runtime_scope ON qc_rule_runtime (test_catalog_id, device_id, active);

CREATE TABLE IF NOT EXISTS raw_instrument_message_runtime (
	id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	protocol VARCHAR(64) NOT NULL, 
	direction VARCHAR(16) NOT NULL, 
	message_type VARCHAR(64), 
	accession_no VARCHAR(64), 
	specimen_barcode VARCHAR(128), 
	parser_version VARCHAR(64) NOT NULL, 
	payload TEXT NOT NULL, 
	parsed_ok BOOLEAN NOT NULL, 
	parse_error TEXT, 
	created_observation_count INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_raw_instrument_message_runtime_accession ON raw_instrument_message_runtime (accession_no);
CREATE INDEX IF NOT EXISTS ix_raw_instrument_message_runtime_device_created ON raw_instrument_message_runtime (device_id, created_at);

CREATE TABLE IF NOT EXISTS task_work_runtime (
	id VARCHAR(36) NOT NULL, 
	group_identifier VARCHAR(128), 
	based_on_order_item_id VARCHAR(36), 
	focus_type VARCHAR(32) NOT NULL, 
	focus_id VARCHAR(36) NOT NULL, 
	queue_code VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	business_status VARCHAR(64), 
	priority VARCHAR(24), 
	owner_user_id VARCHAR(36), 
	owner_practitioner_role_id VARCHAR(36), 
	device_id VARCHAR(36), 
	authored_on DATETIME NOT NULL, 
	started_at DATETIME, 
	completed_at DATETIME, 
	due_at DATETIME, 
	failed_reason TEXT, 
	inputs JSON NOT NULL, 
	outputs JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_user_id) REFERENCES app_user_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_task_work_runtime_owner_status ON task_work_runtime (owner_user_id, status);
CREATE INDEX IF NOT EXISTS ix_task_work_runtime_queue_status ON task_work_runtime (queue_code, status);

CREATE TABLE IF NOT EXISTS analyzer_transport_session_runtime (
	id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	profile_id VARCHAR(36) NOT NULL, 
	session_status VARCHAR(32) NOT NULL, 
	outbound_message_id VARCHAR(36), 
	inbound_message_id VARCHAR(36), 
	expected_inbound_frame_no INTEGER NOT NULL, 
	lease_owner VARCHAR(128), 
	lease_acquired_at DATETIME, 
	lease_expires_at DATETIME, 
	heartbeat_at DATETIME, 
	failure_count INTEGER NOT NULL, 
	next_retry_at DATETIME, 
	last_error TEXT, 
	last_activity_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	closed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id), 
	FOREIGN KEY(profile_id) REFERENCES analyzer_transport_profile_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_transport_session_runtime_device_created ON analyzer_transport_session_runtime (device_id, created_at);
CREATE INDEX IF NOT EXISTS ix_transport_session_runtime_lease_retry ON analyzer_transport_session_runtime (lease_owner, lease_expires_at, next_retry_at);
CREATE INDEX IF NOT EXISTS ix_transport_session_runtime_status ON analyzer_transport_session_runtime (session_status, last_activity_at);

CREATE TABLE IF NOT EXISTS diagnostic_report_runtime (
	id VARCHAR(36) NOT NULL, 
	report_no VARCHAR(64) NOT NULL, 
	order_id VARCHAR(36) NOT NULL, 
	patient_id VARCHAR(36) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	category_code VARCHAR(32) NOT NULL, 
	code_local VARCHAR(128), 
	code_loinc VARCHAR(64), 
	effective_at DATETIME, 
	issued_at DATETIME, 
	conclusion_text TEXT, 
	current_version_no INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (report_no), 
	FOREIGN KEY(order_id) REFERENCES lis_order_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_diagnostic_report_runtime_order_status ON diagnostic_report_runtime (order_id, status);
CREATE INDEX IF NOT EXISTS ix_diagnostic_report_runtime_patient ON diagnostic_report_runtime (patient_id, issued_at);

CREATE TABLE IF NOT EXISTS lis_order_item_runtime (
	id VARCHAR(36) NOT NULL, 
	order_id VARCHAR(36) NOT NULL, 
	line_no INTEGER NOT NULL, 
	test_catalog_id VARCHAR(36) NOT NULL, 
	requested_specimen_type_code VARCHAR(64), 
	status VARCHAR(32) NOT NULL, 
	priority VARCHAR(24), 
	reflex_policy_code VARCHAR(64), 
	aoe_payload JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES lis_order_runtime (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_lis_order_item_runtime_order_status ON lis_order_item_runtime (order_id, status);

CREATE TABLE IF NOT EXISTS qc_run_runtime (
	id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36), 
	status VARCHAR(32) NOT NULL, 
	started_at DATETIME NOT NULL, 
	evaluated_at DATETIME, 
	reviewed_by_user_id VARCHAR(36), 
	summary_json JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lot_id) REFERENCES qc_lot_runtime (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id), 
	FOREIGN KEY(reviewed_by_user_id) REFERENCES app_user_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_qc_run_runtime_device_status ON qc_run_runtime (device_id, status, created_at);
CREATE INDEX IF NOT EXISTS ix_qc_run_runtime_lot_status ON qc_run_runtime (lot_id, status, created_at);

CREATE TABLE IF NOT EXISTS specimen_runtime (
	id VARCHAR(36) NOT NULL, 
	accession_no VARCHAR(64) NOT NULL, 
	order_id VARCHAR(36) NOT NULL, 
	parent_specimen_id VARCHAR(36), 
	patient_id VARCHAR(36) NOT NULL, 
	specimen_type_code VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	collected_at DATETIME, 
	collected_by_practitioner_role_id VARCHAR(36), 
	received_at DATETIME, 
	accepted_at DATETIME, 
	rejected_at DATETIME, 
	rejection_reason_code VARCHAR(64), 
	source_location_id VARCHAR(36), 
	storage_location_id VARCHAR(36), 
	position_code VARCHAR(64), 
	notes TEXT, 
	metadata JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (accession_no), 
	FOREIGN KEY(order_id) REFERENCES lis_order_runtime (id), 
	FOREIGN KEY(parent_specimen_id) REFERENCES specimen_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_specimen_runtime_accession ON specimen_runtime (accession_no);
CREATE INDEX IF NOT EXISTS ix_specimen_runtime_order_status ON specimen_runtime (order_id, status);
CREATE INDEX IF NOT EXISTS ix_specimen_runtime_patient_id ON specimen_runtime (patient_id);

CREATE TABLE IF NOT EXISTS analyzer_transport_message_runtime (
	id VARCHAR(36) NOT NULL, 
	session_id VARCHAR(36) NOT NULL, 
	device_id VARCHAR(36) NOT NULL, 
	direction VARCHAR(16) NOT NULL, 
	protocol VARCHAR(32) NOT NULL, 
	message_type VARCHAR(64) NOT NULL, 
	transport_status VARCHAR(32) NOT NULL, 
	logical_payload TEXT NOT NULL, 
	assembled_payload TEXT, 
	frames_json JSON NOT NULL, 
	total_frames INTEGER NOT NULL, 
	next_frame_index INTEGER NOT NULL, 
	pending_frame_index INTEGER, 
	last_sent_kind VARCHAR(16), 
	retry_count INTEGER NOT NULL, 
	correlation_key VARCHAR(128), 
	ack_deadline_at DATETIME, 
	parse_error TEXT, 
	dispatched_entity_type VARCHAR(64), 
	dispatched_entity_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	completed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES analyzer_transport_session_runtime (id), 
	FOREIGN KEY(device_id) REFERENCES device_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_transport_message_runtime_session_status ON analyzer_transport_message_runtime (session_id, direction, transport_status, created_at);

CREATE TABLE IF NOT EXISTS container_runtime (
	id VARCHAR(36) NOT NULL, 
	specimen_id VARCHAR(36) NOT NULL, 
	parent_container_id VARCHAR(36), 
	barcode VARCHAR(128) NOT NULL, 
	container_type_code VARCHAR(64) NOT NULL, 
	position_code VARCHAR(64), 
	volume_value FLOAT, 
	volume_ucum VARCHAR(32), 
	storage_location_id VARCHAR(36), 
	status VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(specimen_id) REFERENCES specimen_runtime (id), 
	FOREIGN KEY(parent_container_id) REFERENCES container_runtime (id), 
	UNIQUE (barcode)
);
CREATE INDEX IF NOT EXISTS ix_container_runtime_barcode ON container_runtime (barcode);
CREATE INDEX IF NOT EXISTS ix_container_runtime_specimen ON container_runtime (specimen_id, created_at);

CREATE TABLE IF NOT EXISTS diagnostic_report_version_runtime (
	id VARCHAR(36) NOT NULL, 
	report_id VARCHAR(36) NOT NULL, 
	version_no INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	amendment_reason TEXT, 
	rendered_pdf_uri VARCHAR(255), 
	signed_by_user_id VARCHAR(36), 
	signed_at DATETIME, 
	payload JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES diagnostic_report_runtime (id), 
	FOREIGN KEY(signed_by_user_id) REFERENCES app_user_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_diagnostic_report_version_runtime_report ON diagnostic_report_version_runtime (report_id, version_no);

CREATE TABLE IF NOT EXISTS observation_runtime (
	id VARCHAR(36) NOT NULL, 
	order_item_id VARCHAR(36) NOT NULL, 
	specimen_id VARCHAR(36), 
	code_local VARCHAR(128) NOT NULL, 
	code_loinc VARCHAR(64), 
	status VARCHAR(32) NOT NULL, 
	category_code VARCHAR(32) NOT NULL, 
	value_type VARCHAR(32) NOT NULL, 
	value_num FLOAT, 
	value_text TEXT, 
	value_boolean BOOLEAN, 
	value_code_system VARCHAR(128), 
	value_code VARCHAR(128), 
	unit_ucum VARCHAR(32), 
	interpretation_code VARCHAR(64), 
	abnormal_flag VARCHAR(64), 
	method_code VARCHAR(64), 
	device_id VARCHAR(36), 
	raw_message_id VARCHAR(36), 
	effective_at DATETIME, 
	issued_at DATETIME, 
	reference_interval_snapshot JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_item_id) REFERENCES lis_order_item_runtime (id), 
	FOREIGN KEY(specimen_id) REFERENCES specimen_runtime (id), 
	FOREIGN KEY(raw_message_id) REFERENCES raw_instrument_message_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_observation_runtime_code_loinc ON observation_runtime (code_loinc);
CREATE INDEX IF NOT EXISTS ix_observation_runtime_order_item_status ON observation_runtime (order_item_id, status);
CREATE INDEX IF NOT EXISTS ix_observation_runtime_specimen ON observation_runtime (specimen_id);

CREATE TABLE IF NOT EXISTS qc_result_runtime (
	id VARCHAR(36) NOT NULL, 
	run_id VARCHAR(36) NOT NULL, 
	test_catalog_id VARCHAR(36) NOT NULL, 
	value_num FLOAT NOT NULL, 
	unit_ucum VARCHAR(32), 
	decision VARCHAR(32), 
	z_score FLOAT, 
	warning_rules_json JSON NOT NULL, 
	failure_rules_json JSON NOT NULL, 
	observed_at DATETIME, 
	evaluated_at DATETIME, 
	raw_message_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(run_id) REFERENCES qc_run_runtime (id), 
	FOREIGN KEY(test_catalog_id) REFERENCES test_catalog_runtime (id), 
	FOREIGN KEY(raw_message_id) REFERENCES raw_instrument_message_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_qc_result_runtime_run_created ON qc_result_runtime (run_id, created_at);
CREATE INDEX IF NOT EXISTS ix_qc_result_runtime_test_eval ON qc_result_runtime (test_catalog_id, evaluated_at);

CREATE TABLE IF NOT EXISTS specimen_event_runtime (
	id VARCHAR(36) NOT NULL, 
	specimen_id VARCHAR(36) NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	performed_by_user_id VARCHAR(36), 
	location_id VARCHAR(36), 
	occurred_at DATETIME NOT NULL, 
	details JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(specimen_id) REFERENCES specimen_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_specimen_event_runtime_specimen ON specimen_event_runtime (specimen_id, occurred_at);

CREATE TABLE IF NOT EXISTS analyzer_transport_frame_log_runtime (
	id VARCHAR(36) NOT NULL, 
	session_id VARCHAR(36) NOT NULL, 
	message_id VARCHAR(36), 
	direction VARCHAR(16) NOT NULL, 
	event_kind VARCHAR(16) NOT NULL, 
	control_code VARCHAR(16), 
	frame_no INTEGER, 
	payload_chunk TEXT, 
	framed_payload TEXT, 
	checksum_hex VARCHAR(8), 
	is_final BOOLEAN, 
	accepted BOOLEAN NOT NULL, 
	duplicate_flag BOOLEAN NOT NULL, 
	retry_no INTEGER NOT NULL, 
	notes TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES analyzer_transport_session_runtime (id), 
	FOREIGN KEY(message_id) REFERENCES analyzer_transport_message_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_transport_frame_runtime_message ON analyzer_transport_frame_log_runtime (message_id, created_at);
CREATE INDEX IF NOT EXISTS ix_transport_frame_runtime_session ON analyzer_transport_frame_log_runtime (session_id, created_at);

CREATE TABLE IF NOT EXISTS autoverification_run_runtime (
	id VARCHAR(36) NOT NULL, 
	observation_id VARCHAR(36) NOT NULL, 
	rule_id VARCHAR(36), 
	decision VARCHAR(32) NOT NULL, 
	reasons_json JSON NOT NULL, 
	evaluated_at DATETIME NOT NULL, 
	created_task_id VARCHAR(36), 
	PRIMARY KEY (id), 
	FOREIGN KEY(observation_id) REFERENCES observation_runtime (id), 
	FOREIGN KEY(rule_id) REFERENCES autoverification_rule_runtime (id), 
	FOREIGN KEY(created_task_id) REFERENCES task_work_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_autoverification_run_runtime_observation ON autoverification_run_runtime (observation_id, evaluated_at);

CREATE TABLE IF NOT EXISTS observation_link_runtime (
	id VARCHAR(36) NOT NULL, 
	source_observation_id VARCHAR(36) NOT NULL, 
	target_observation_id VARCHAR(36) NOT NULL, 
	relation_type VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_observation_id) REFERENCES observation_runtime (id), 
	FOREIGN KEY(target_observation_id) REFERENCES observation_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_observation_link_runtime_source ON observation_link_runtime (source_observation_id, relation_type);

CREATE TABLE IF NOT EXISTS report_observation_runtime (
	id VARCHAR(36) NOT NULL, 
	report_id VARCHAR(36) NOT NULL, 
	observation_id VARCHAR(36) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(report_id) REFERENCES diagnostic_report_runtime (id), 
	FOREIGN KEY(observation_id) REFERENCES observation_runtime (id)
);
CREATE INDEX IF NOT EXISTS ix_report_observation_runtime_report ON report_observation_runtime (report_id, sort_order);
