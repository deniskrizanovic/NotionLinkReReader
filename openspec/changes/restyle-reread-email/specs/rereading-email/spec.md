## ADDED Requirements

### Requirement: HTML email is a styled, self-contained document
The composed HTML email SHALL be a complete HTML document that renders as a single
centered card containing a header, one row per selected link, and a footer, so it
reads as a finished message rather than a bare list of fields.

#### Scenario: Composed HTML is a full document
> **Tests:** none
- **GIVEN** one or more selected link records
- **WHEN** the email is composed
- **THEN** the HTML is a complete document with a document type declaration and a head that declares support for light and dark color schemes
- **AND** the links are laid out as a centered fixed-width card on a light background

#### Scenario: Header shows count and date
> **Tests:** none
- **GIVEN** a selection of N link records for a given run date
- **WHEN** the email is composed
- **THEN** the header shows the number of links selected and the run date
- **AND** a footer identifies the message as sent by NotionLinkReReader

### Requirement: Each link renders as a scannable row
The system SHALL render each selected link as its own row showing the name as a
hyperlink to its Notion page, the external url as a hyperlink, the reason, and the
tags as individual pill badges.

#### Scenario: Link row with all fields
> **Tests:** none
- **GIVEN** a selected link record with a name, page URL, url, reason, and tags
- **WHEN** the email is composed
- **THEN** the row shows the name as a link opening the Notion page, the url as a clickable link, the reason text, and each tag as its own pill badge

#### Scenario: Optional field is unset
> **Tests:** none
- **GIVEN** a selected link record whose reason, url, or tags are unset
- **WHEN** the email is composed
- **THEN** the reason renders as a muted placeholder, the url line is omitted, and no tag pills are shown, while the row still renders cleanly

### Requirement: Empty-state email shares the styled shell
The empty-state email SHALL use the same document shell as the populated email so
every run produces a consistently styled, observable message.

#### Scenario: No links selected
> **Tests:** none
- **GIVEN** a run whose selection contains zero link records
- **WHEN** the email is composed
- **THEN** the recipient receives a styled email using the same shell that states no links were found today
