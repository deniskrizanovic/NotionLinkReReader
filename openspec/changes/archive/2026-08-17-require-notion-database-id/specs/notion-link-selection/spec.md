## MODIFIED Requirements

### Requirement: Query the configured Notion database
The system SHALL query the Notion database identified by the configured database id, using the configured integration token, and retrieve all of its rows, following pagination until every row has been fetched. The database id SHALL be supplied entirely from the environment; the system SHALL NOT embed any database id default in source, so an unset database id fails fast rather than silently targeting an embedded database.

#### Scenario: Database returns rows
> **Tests:** test_query_follows_pagination
- **GIVEN** a valid integration token and a database id shared with that integration
- **WHEN** the job queries the database
- **THEN** the system receives the database rows for normalization

#### Scenario: Database exceeds one page of rows
> **Tests:** test_query_follows_pagination
- **GIVEN** a database whose row count exceeds a single Notion response page
- **WHEN** the job queries the database
- **THEN** the system follows the pagination cursor until exhausted so that every row across all pages is eligible for selection

#### Scenario: Missing required configuration
> **Tests:** test_missing_required_var_raises_naming_it
- **GIVEN** the integration token or database id is absent from the environment
- **WHEN** the job starts
- **THEN** the system fails fast with an error naming the missing configuration before any network call

#### Scenario: Database id unset with no embedded default
> **Tests:** test_missing_database_id_raises_naming_it
- **GIVEN** the environment does not set the database id and no database id default exists in source
- **WHEN** the job starts
- **THEN** the system fails fast with an error naming the missing database id rather than querying any embedded database

#### Scenario: Notion query fails
> **Tests:** test_query_failure_logs_and_reraises
- **GIVEN** the database id is not shared with the integration or the token is invalid
- **WHEN** the job queries the database
- **THEN** the system logs the error and re-throws it rather than sending a partial email
