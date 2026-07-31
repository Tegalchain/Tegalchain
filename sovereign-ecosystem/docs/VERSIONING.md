# Sovereign Ecosystem Versioning

Three independent version lines. **Do not** tie them to a single global number.

## 1. Zeegate product generation (major Android releases)

| Generation | Meaning | Android `versionName` major |
|------------|---------|----------------------------|
| **Zeegate v1** | gsm2sip + AnyFi + GreTelemetry agent scaffold (current import) | `1.x.y` |
| **Zeegate v2** | tegalid-gated edge + Kamailio/FS voice lab integration | `2.x.y` |
| **Zeegate v3+** | Fleet hardening, future features | `3.x.y`, … |

**Rules**

- **Major** `versionName` = product generation (`1.0.0` → Zeegate v1, `2.0.0` → Zeegate v2).
- **Minor** = backward-compatible features within a generation.
- **Patch** = bugfixes only.
- **`versionCode`** = monotonic integer; increment on every Play/system release (never reuse).

Canonical source: `zeegate/VERSION` + `zeegate/app/build.gradle.kts`.

## 2. Greentelemetry protocol (cross-subsystem contract)

**Glossary:** `gretelemetry` = greentelemetry protocol; `GreTelemetry` = Zeegate Android client — [GLOSSARY.md](./GLOSSARY.md).

Versioned separately in `greentelemetry-protocol-spec/VERSION`.

- **MAJOR** — breaking telemetry shape or required fields.
- **MINOR** — new optional metrics (backward compatible).
- **PATCH** — documentation/clarifications only.

When protocol MAJOR changes:

1. Add `greentelemetry-protocol-spec/schema/vN/schema.json` (or bump with migration notes).
2. Update `greentelemetry_protocol_spec` validators.
3. Document minimum Zeegate / Bytenergy / cloud versions in `VERSIONS.json`.

Current protocol: **1.0.0** (Zeegate: `telecom_bandwidth_bytes`; Bytenergy: `energy_generation_kwh`).

Scope: Zerocell Zeegate, Bytenergy Utility, and future environmentally sustainable nodes — add new `system_type` values via **minor** protocol bumps (see [greentelemetry-protocol-spec/README.md](../greentelemetry-protocol-spec/README.md)).

## 3. Sovereign-ecosystem monorepo

Root `VERSIONS.json` tracks release bundles for GitHub tags and ops.

- Ecosystem semver is **informational** (e.g. `0.1.0` until first production cut).
- Subcomponents keep their own versions.

## Git tags (recommended)

```
ecosystem/v0.1.0          # monorepo release
protocol/v1.0.0           # schema + Python bindings
zeegate/v1.0.0            # Android APK generation 1
tegalchain-bridge/v0.1.0  # mint/identity Python module (optional)
```

## Compatibility matrix (update each release)

| Ecosystem | Protocol | Zeegate gen | Notes |
|-----------|----------|-------------|-------|
| 0.1.0 | 1.0.0 | v1 (1.0.x) | Initial monorepo import |

## Release checklist

1. Bump component version(s) in `VERSIONS.json` and component `VERSION` files.
2. Update compatibility matrix above.
3. Update `zeegate/CHANGELOG.md` for Android releases.
4. `git tag zeegate/vX.Y.Z` (and other tags as needed).
5. Push tags to GitHub.
