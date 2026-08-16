# scheduled-run Specification

## Purpose

Run the job once per weekday at 11:00 local time on macOS via `launchd`, with all configuration supplied from the environment.

## Requirements

### Requirement: Run weekdays at 11:00 local time
The system SHALL run the job once per day at 11:00 local time on weekdays (Monday through Friday) on macOS via a `launchd` calendar schedule, and SHALL NOT run on Saturday or Sunday.

#### Scenario: Scheduled fire while awake
> **Tests:** none
- **GIVEN** an installed `launchd` agent scheduled for 11:00 local time on weekdays and a machine that is awake at that time
- **WHEN** the clock reaches 11:00 on a weekday
- **THEN** the job runs once and produces a sent email

#### Scenario: No run on weekends
> **Tests:** none
- **GIVEN** an installed `launchd` agent scheduled for weekdays only
- **WHEN** the clock reaches 11:00 on Saturday or Sunday
- **THEN** the job does not run

#### Scenario: Catch-up after sleep
> **Tests:** none
- **GIVEN** an installed `launchd` agent scheduled for 11:00 on weekdays and a machine asleep at that time
- **WHEN** the machine wakes after 11:00 on a weekday
- **THEN** `launchd` runs the missed job once on wake

### Requirement: Run the job with configuration from the environment
The system SHALL execute the job entrypoint with all secrets and identifiers supplied from the environment, keeping no secrets in the scheduled definition or the repository.

#### Scenario: Entrypoint invoked with environment configuration
> **Tests:** none
- **GIVEN** an environment providing the Notion token, database id, Gmail credentials, and recipient
- **WHEN** the scheduled agent triggers the entrypoint
- **THEN** the job reads its configuration from the environment and runs without any secret stored in the schedule definition or repository
