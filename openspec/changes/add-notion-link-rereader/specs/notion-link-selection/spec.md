## ADDED Requirements

### Requirement: Query the configured Notion database
The system SHALL query the Notion database identified by the configured database id, using the configured integration token, and retrieve all of its rows, following pagination until every row has been fetched.

#### Scenario: Database returns rows
> **Tests:** none
- **GIVEN** a valid integration token and a database id shared with that integration
- **WHEN** the job queries the database
- **THEN** the system receives the database rows for normalization

#### Scenario: Database exceeds one page of rows
> **Tests:** test_query_follows_pagination
- **GIVEN** a database whose row count exceeds a single Notion response page
- **WHEN** the job queries the database
- **THEN** the system follows the pagination cursor until exhausted so that every row across all pages is eligible for selection

#### Scenario: Missing required configuration
> **Tests:** none
- **GIVEN** the integration token or database id is absent from the environment
- **WHEN** the job starts
- **THEN** the system fails fast with an error naming the missing configuration before any network call

#### Scenario: Notion query fails
> **Tests:** none
- **GIVEN** the database id is not shared with the integration or the token is invalid
- **WHEN** the job queries the database
- **THEN** the system logs the error and re-throws it rather than sending a partial email

### Requirement: Normalize rows into link records
The system SHALL map each Notion row into a link record with the fields name, page URL, url, reason, and tags, treating any absent or empty property value as unset.

#### Scenario: Row with all fields populated
> **Tests:** none
- **GIVEN** a Notion row with a title, a url, a reason, and one or more tags
- **WHEN** the row is normalized
- **THEN** the link record carries the name text, the row's Notion page URL, the url value, the reason text, and the tag list

#### Scenario: Row missing optional fields
> **Tests:** none
- **GIVEN** a Notion row whose url, reason, or tags property is empty
- **WHEN** the row is normalized
- **THEN** the corresponding link record fields are unset rather than raising an error

### Requirement: Select up to three links at random
The system SHALL select up to three link records at random without replacement, returning all records when fewer than three exist and an empty selection when none exist.

#### Scenario: More than three rows available
> **Tests:** none
- **GIVEN** a normalized set of more than three link records
- **WHEN** the system selects links
- **THEN** exactly three distinct records are chosen at random

#### Scenario: Fewer than three rows available
> **Tests:** none
- **GIVEN** a normalized set of one or two link records
- **WHEN** the system selects links
- **THEN** all available records are chosen and none is duplicated

#### Scenario: No rows available
> **Tests:** none
- **GIVEN** a normalized set containing zero link records
- **WHEN** the system selects links
- **THEN** the selection is empty and no error is raised

#### Scenario: Selection allows repeats across runs
> **Tests:** none
- **GIVEN** a link record selected on a previous run
- **WHEN** the system selects links on a later run
- **THEN** the same record MAY be selected again because selection keeps no state
