# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

- Add ``upkie_locomotion.envs.register`` function
- PPO balancer: setting for total number of training timesteps
- UpkieWheelsEnv: simple example

### Changed

- UpkieWheelsEnv: remove dependency on gin

## [0.2.0] - 2023/03/03

### Added

- Agent: PPO balancer
- Environment: ``UpkieWheelsEnv-v1``
- Observers: Base pitch

### Changed

- Promote ``utils.imu`` to a proper Python observer
- Switch from ``aiorate`` to ``loop_rate_limiters``

### Fixed

- Document both C++ and Python code with Doxygen
- Python requirements and dependencies in Bazel

## [0.1.0] - 2022/09/12

Starting this changelog.
