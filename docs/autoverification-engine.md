# Autoverification Engine

The v6 slice adds a first practical rules engine for result autoverification.

## What It Covers

- global rules or rules scoped to `test_catalog`, `device`, or `specimen_type_code`
- dry-run evaluation without changing result state
- apply mode that either auto-finalizes an observation or holds it for manual review
- append-only run logging through `autoverification_run`
- provenance for both finalize and hold decisions

## Supported Conditions

The current `condition` payload supports:

- `specimen_status_in`
- `require_value`
- `unit_ucum_equals`
- `allowed_abnormal_flags`
- `disallow_abnormal_flags`
- `require_reference_interval`
- `require_within_reference_interval`
- `disallow_reference_critical`
- `allowed_interpretation_codes`
- `disallow_interpretation_codes`
- `numeric_min`
- `numeric_max`
- `critical_low`
- `critical_high`
- `require_previous_final`
- `delta_previous_max_age_hours`
- `delta_require_same_unit`
- `delta_abs_max`
- `delta_percent_max`

## API Surface

- `POST /api/v1/autoverification/rules`
- `GET /api/v1/autoverification/rules`
- `GET /api/v1/autoverification/rules/{rule_id}`
- `POST /api/v1/autoverification/observations/{observation_id}/evaluate`
- `POST /api/v1/autoverification/observations/{observation_id}/apply`
- `GET /api/v1/autoverification/observations/{observation_id}/runs`

## Apply Behavior

When evaluation passes:

- observation status moves to `final`
- `issued_at` is stamped
- the related order item moves to `released`
- provenance is written with an activity ending in `-finalize`

When evaluation fails:

- observation stays `preliminary`
- the related order item moves to `tech_review`
- a `manual-review` task is created or reused
- provenance is written with an activity ending in `-hold`

## Current Boundary

- rules are stored as JSON conditions, not a versioned DSL
- delta checks use the latest `final`, `corrected`, or `amended` result for the same patient and `code_local`
- QC gate is now consulted before autoverification may auto-finalize an observation
- richer clinical rules still remain starter-level and do not yet cover broader patient context, diagnoses, or section-specific policies
- there is no site-specific release workflow for rule promotion yet
