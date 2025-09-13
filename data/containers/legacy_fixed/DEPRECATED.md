# DEPRECATED

These legacy container files are deprecated and should not be used for new development.

**Use instead**: `data/containers/v1/` - Container Standard v1.0 compliant files

## Migration

All containers in this directory have been converted to v1.0 format and are available in:
- `data/containers/v1/`

## Conversion Details

- **Format**: Legacy format → Container Standard v1.0
- **Designer**: Anton Bakker
- **Date**: 2025-09-12
- **Tool**: `tools/convert_legacy_containers.py`
- **Validation**: All 27 containers pass v1.0 validation

## Container Standard v1.0

See `docs/CONTAINER_STANDARD.md` for the current specification.

**Key changes**:
- Added `version`, `cid`, `designer` fields
- Changed `coordinates` to `cells`
- Removed `name`, `lattice_type` fields
- Deterministic CID computation with FCC canonicalization
