# SmartPark AI Change Log

## 2026-06-11

### Fixed
- Replaced the deprecated `djongo` database backend with `django-mongodb-backend` and modern MongoDB dependencies.
- Pinned the backend to Django 5.2-compatible versions and updated `django-filter` to a supported release.
- Added `@supabase/supabase-js` to the frontend dependency set and updated env example files.
- Fixed the duplicate `plugins` configuration in the occupancy chart component.
- Added a CLI launcher for backend, frontend, edge AI, and model training commands.
- Refreshed the project documentation to reflect the updated stack.

### Added
- SmartPark CLI launcher: `smartpark-cli.py`
- Audit report: `ERROR_REPORT.md`
