# Changelog

## 1.0.0 — 2026-04-15

Initial public release as a fork of [vitals5/ha_scrutiny](https://github.com/vitals5/ha_scrutiny).

This release is a substantial rewrite addressing every open issue and pending PR on the upstream
repository at the time of the fork, plus a full Home Assistant quality scale compliance pass.

### New features

- **HTTPS / full URL configuration** — configure using a full URL (e.g.
  `http://scrutiny.local:8080` or `https://scrutiny.example.com`) instead of separate
  host and port fields. A **Verify SSL certificate** toggle handles self-signed certificates.
  *(Addresses [vitals5#38](https://github.com/vitals5/ha_scrutiny/issues/38))*

- **Last SMART Update sensor** — a new `TIMESTAMP` entity per disk showing when Scrutiny
  last received SMART data from its collector. Makes data staleness immediately visible and
  automation-ready (e.g. alert if no update in 48 hours). Implemented as a proper entity
  rather than an attribute so it graphs over time and integrates with HA history.
  *(Addresses [vitals5#9](https://github.com/vitals5/ha_scrutiny/issues/9),
  [vitals5#14](https://github.com/vitals5/ha_scrutiny/pull/14))*

- **Serial number in device name** — disk devices are named `Model (SerialNumber)` (e.g.
  `WD Red Plus 4TB (WD40EFZX-12345)`) so they cross-reference cleanly against TrueNAS,
  ZFS, smartctl, and other tools. The stable device identity in HA remains the WWN.
  *(Addresses [vitals5#41](https://github.com/vitals5/ha_scrutiny/issues/41))*

- **Deep-link Visit button on each disk device** — clicking Visit on a disk device opens
  its detail page directly in the Scrutiny web UI (`/web/device/{wwn}`), not just the root.

- **SMART attribute sensors with pass/fail status and raw value history** — two sensor
  tiers for each SMART attribute: a status sensor (Passed / Warning / Failed) and an
  optional companion numeric sensor for the raw integer value. The raw value sensor has
  `state_class=MEASUREMENT` so Home Assistant records its full history and long-term
  statistics, making gradual degradation trends visible over time (e.g. a slowly climbing
  Reallocated Sectors Count). All attribute sensors are opt-in; raw value sensors require
  both the attribute tier and the **Enable raw value sensors** toggle to be enabled.
  *(Addresses [vitals5#39](https://github.com/vitals5/ha_scrutiny/issues/39))*


- **Archived disk support** — archived drives are hidden by default; a **Show archived
  disks** toggle re-surfaces them with an `[Archived]` suffix on the device name.

- **Stale device cleanup** — devices for disks no longer present in Scrutiny are removed
  automatically after each successful poll, keeping the HA device list in sync.

- **Configurable poll interval and entity tiers** — scan interval, archived disk
  visibility, and SMART attribute sensor level are all adjustable via the Configure screen
  without removing and re-adding the integration.

- **Reconfigure flow** — the URL and SSL settings can be updated via the three-dot
  Reconfigure menu without losing options or entity history.

- **Hub device with Visit link** — a service-type hub device represents the Scrutiny
  instance itself, with a Visit link to the web UI root.

### Reliability improvements

- **Concurrency-limited detail fetching** — detail requests for individual disks are now
  limited to 5 simultaneous requests using an `asyncio.Semaphore`. On large installations
  (20+ disks) this prevents CPU spikes and timeout errors on resource-constrained Scrutiny
  containers, while adding zero overhead for typical deployments.
  *(Addresses [vitals5#33](https://github.com/vitals5/ha_scrutiny/pull/33))*

- **Per-disk detail failure isolation** — if fetching details for one disk fails, the
  remaining disks continue to update normally. Sensors for the failed disk fall back to
  summary data rather than going unavailable.

- **Graceful coordinator error handling** — connection errors, API errors, and unexpected
  errors are all caught separately and surfaced as `UpdateFailed` so HA handles retry and
  unavailability correctly without filling logs unnecessarily.

- **API request timeout raised to 15 s** — provides headroom for Scrutiny instances under
  load without the excessive 30 s delay that would stall HA on genuine outages.

### Home Assistant quality scale

All Bronze, Silver, Gold, and Platinum quality scale rules are satisfied. Notable
compliance items: strict typing with `py.typed`, full entity and icon translations,
`DataUpdateCoordinator` with explicit `config_entry`, `PARALLEL_UPDATES = 0`,
`async_get_clientsession` for websession injection, reconfigure flow, diagnostics
download, `entity_registry_enabled_default` via opt-in creation rather than
disable-by-default. The `quality_scale` field in `manifest.json` is set to `gold`,
which is the maximum value the field accepts; Platinum is assessed separately by the HA
core team for integrations submitted to core.

## 1.0.1 — 2026-04-18

### Bug fixes

- **Raw value sensor names** — all raw value sensors were displaying "Raw Value" as
  their name instead of the attribute name (e.g. "Reallocated Sectors Count (Raw)").
  Caused by the `translation_key` on the sensor description overriding the
  programmatically set name. Fixed by removing the translation key and setting the icon
  directly via `_attr_icon`.

### CI fixes

- **Tests failing in CI with `ModuleNotFoundError`** — `pythonpath = .` added to
  `pytest.ini` so pytest adds the repo root to `sys.path` in clean CI environments.
  Also added `asyncio_default_fixture_loop_scope = function` to silence a
  pytest-asyncio deprecation warning.

- **Test teardown error in `test_config_flow_user_step_success`** — creating a config
  entry in the flow triggered a real `async_setup_entry`, which attempted a network call,
  crashed, and left a background retry thread running into teardown. Fixed by mocking
  `async_setup_entry` in the two tests that reach `CREATE_ENTRY`.

- **GitHub Actions Node.js 20 deprecation warnings** — updated `actions/checkout` from
  `v4` to `v6` and `actions/setup-python` from `v5` to `v6` across all workflow files.
  Both v6 releases run on Node.js 24.
