# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2025-11-12

### Added

- **Enhanced Git Sync Error Handling**: Improved error messages for common sync failures
  - Specific detection and guidance for non-fast-forward push errors
  - Better diagnostics for authentication and connectivity issues
- **Sync Connectivity Checker**: New `turboalias sync check` command to diagnose sync issues
- **Reliable Auto-Sync**: Fixed background auto-sync to work consistently
  - Changed from daemon to non-daemon thread with 2-second timeout

### Fixed

- **Auto-sync reliability**: Background sync now completes successfully on every change
- **Non-fast-forward push errors**: Now provides clear guidance instead of generic error messages
- **Thread lifecycle**: Auto-sync threads no longer terminate prematurely

### Improved

- Error messages now include specific diagnoses and fix suggestions
- Better logging of sync errors for debugging
- More helpful output for multi-account GitHub setups

⚠️ **This is an early development release (0.0.x). The API and features are not stable and may change.**

## [0.0.4] - 2025-11-10

### Added

- **Git Sync functionality**: Sync aliases across machines using Git
- Version display in help message and `--version` flag

### Changed

- Improved code readability with better method naming
- Removed duplicate code and unused variables
- Enhanced `nuke` command warning message for clarity

### Fixed

- Code refactoring for better maintainability

### Note

⚠️ **This is an early development release (0.0.x). The API and features are not stable and may change.**

## [0.0.3] - 2025-11-09

### Changed

- Improved CI/CD pipeline for PyPI publishing
- Updated GitHub Actions workflows

### Note

⚠️ **This is an early development release (0.0.x). The API and features are not stable and may change.**

## [0.0.2] - (Previous release)

### Added

- Initial release with basic alias management
- Support for bash and zsh
- Category organization
- Import existing aliases

## [0.0.1] - (Initial)

### Added

- First public release
