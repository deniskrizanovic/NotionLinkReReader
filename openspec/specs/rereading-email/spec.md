# rereading-email Specification

## Purpose

Compose and send the daily rereading email over Gmail, always sending — including an explicit empty state.

## Requirements

### Requirement: Compose the rereading email
The system SHALL compose an email for the selected links that carries both an HTML part and a plain-text alternative part.

#### Scenario: Email includes a plain-text alternative
> **Tests:** test_message_has_both_mime_parts
- **GIVEN** one or more selected link records
- **WHEN** the email is composed
- **THEN** the message carries both an HTML part with clickable links and a plain-text alternative part

### Requirement: HTML email is a styled, self-contained document
The composed HTML email SHALL be a complete HTML document that renders as a single
centered card containing a header, one row per selected link, and a footer, so it
reads as a finished message rather than a bare list of fields.

#### Scenario: Composed HTML is a full document
> **Tests:** test_html_document_shell
- **GIVEN** one or more selected link records
- **WHEN** the email is composed
- **THEN** the HTML is a complete document with a document type declaration and a head that declares support for light and dark color schemes
- **AND** the links are laid out as a centered fixed-width card on a light background

#### Scenario: Header shows count and date
> **Tests:** test_html_header_shows_count_and_date, test_html_footer_identifies_sender
- **GIVEN** a selection of N link records for a given run date
- **WHEN** the email is composed
- **THEN** the header shows the number of links selected and the run date
- **AND** a footer identifies the message as sent by NotionLinkReReader

### Requirement: Each link renders as a scannable row
The system SHALL render each selected link as its own row showing the name as a
hyperlink to its Notion page, the external url as a hyperlink, the reason, and the
tags as individual pill badges.

#### Scenario: Link row with all fields
> **Tests:** test_html_renders_all_fields_with_links
- **GIVEN** a selected link record with a name, page URL, url, reason, and tags
- **WHEN** the email is composed
- **THEN** the row shows the name as a link opening the Notion page, the url as a clickable link, the reason text, and each tag as its own pill badge

#### Scenario: Optional field is unset
> **Tests:** test_html_unset_fields_render_cleanly
- **GIVEN** a selected link record whose reason, url, or tags are unset
- **WHEN** the email is composed
- **THEN** the reason renders as a muted placeholder, the url line is omitted, and no tag pills are shown, while the row still renders cleanly

### Requirement: Send the email via Gmail
The system SHALL send the composed email to the configured recipient over Gmail SMTP authenticated with the configured Gmail address and app password.

#### Scenario: Email sent successfully
> **Tests:** test_send_message_delivers_over_starttls
- **GIVEN** valid Gmail credentials and a recipient address in the environment
- **WHEN** the composed email is sent
- **THEN** the message is delivered to the recipient over an encrypted SMTP connection

#### Scenario: Send fails
> **Tests:** test_send_failure_logs_and_reraises
- **GIVEN** invalid Gmail credentials or an unreachable SMTP server
- **WHEN** the system attempts to send
- **THEN** the system logs the failure and re-throws it

### Requirement: Always send, including the empty state
The system SHALL send an email on every run, sending an explicit empty-state message when no links were selected, styled with the same document shell as a populated email.

#### Scenario: No links selected
> **Tests:** test_empty_state_uses_styled_shell, test_empty_message_subject_differs
- **GIVEN** a run whose selection contains zero link records
- **WHEN** the email is composed and sent
- **THEN** the recipient receives a styled email using the same shell that states no links were found today, so the successful run is observable
