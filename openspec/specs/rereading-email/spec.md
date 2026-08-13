# rereading-email Specification

## Purpose

Compose and send the daily rereading email over Gmail, always sending — including an explicit empty state.

## Requirements

### Requirement: Compose the rereading email
The system SHALL compose an HTML email containing one section per selected link, rendering the name as a hyperlink to its Notion page and the url as a hyperlink to the external site, and showing the reason and tags.

#### Scenario: Selected link rendered with all fields
> **Tests:** none
- **GIVEN** a selected link record with a name, page URL, url, reason, and tags
- **WHEN** the email is composed
- **THEN** the section shows the name as a link opening the Notion page, the url as a link opening the external site, the reason text, and the tags as a comma-separated list

#### Scenario: Field value is unset
> **Tests:** none
- **GIVEN** a selected link record whose reason, tags, or url is unset
- **WHEN** the email is composed
- **THEN** the missing value is rendered as an em dash

#### Scenario: Email includes a plain-text alternative
> **Tests:** none
- **GIVEN** one or more selected link records
- **WHEN** the email is composed
- **THEN** the message carries both an HTML part with clickable links and a plain-text alternative part

### Requirement: Send the email via Gmail
The system SHALL send the composed email to the configured recipient over Gmail SMTP authenticated with the configured Gmail address and app password.

#### Scenario: Email sent successfully
> **Tests:** none
- **GIVEN** valid Gmail credentials and a recipient address in the environment
- **WHEN** the composed email is sent
- **THEN** the message is delivered to the recipient over an encrypted SMTP connection

#### Scenario: Send fails
> **Tests:** none
- **GIVEN** invalid Gmail credentials or an unreachable SMTP server
- **WHEN** the system attempts to send
- **THEN** the system logs the failure and re-throws it

### Requirement: Always send, including the empty state
The system SHALL send an email on every run, sending an explicit empty-state message when no links were selected.

#### Scenario: No links selected
> **Tests:** none
- **GIVEN** a run whose selection contains zero link records
- **WHEN** the email is composed and sent
- **THEN** the recipient receives an email stating no links were found today so the successful run is observable
