# Ledger Change Control

This directory provides a lightweight, file-based system for managing defects, features, and other planned changes to the Ledger application.

The approach is intended to remain simple, readable, version-controlled, and suitable for a project where changes often span the Angular client, Java server, database, deployment scripts, and documentation.

## Directory Structure

```text
change-control/
├── README.md
├── INDEX.md
├── todo/
├── in-progress/
└── completed/
```

The folders represent the current state of each change:

- `todo` — accepted items that have not yet been started
- `in-progress` — items currently being investigated or implemented
- `completed` — finished items retained as a permanent record

Each defect or feature should have its own folder. The whole folder moves between the status directories as work progresses.

Example:

```text
change-control/
├── todo/
│   └── FEAT-0002-customer-search/
│       ├── README.md
│       ├── evidence/
│       ├── designs/
│       └── notes/
├── in-progress/
│   └── DEF-0001-login-fails-after-token-expiry/
│       ├── README.md
│       ├── evidence/
│       └── notes/
└── completed/
```

## Change Identifiers

Every change should be given a permanent identifier when it is created.

Suggested prefixes:

- `DEF` — defect
- `FEAT` — feature
- `CHG` — general technical or operational change

Examples:

```text
DEF-0001-login-fails-after-token-expiry
FEAT-0002-customer-search
CHG-0003-update-deployment-backup-process
```

The identifier must not change when the folder moves between `todo`, `in-progress`, and `completed`.

## Change Item Contents

Every change folder should contain a `README.md` as its main record.

Supporting material can be placed in subdirectories such as:

```text
evidence/
designs/
notes/
sql/
logs/
screenshots/
```

Typical supporting material includes:

- browser console logs
- Java server logs
- screenshots
- API requests and responses
- SQL queries and results
- database migration notes
- design sketches
- test results
- deployment output

Raw evidence should be kept separate from the main `README.md` so that the change description remains readable.

## Change Item Template

The following template can be used for each item.

```markdown
# DEF-0001 — Login fails after token expiry

## Type

Defect

## Status

To do

## Priority

High

## Opened

YYYY-MM-DD

## Summary

Provide a short description of the defect or feature.

## Background

Describe why the change is required and any relevant history.

## Observed Behaviour

For a defect, describe what currently happens.

For a feature, describe the current limitation.

## Expected Behaviour

Describe what the system should do after the change is complete.

## Reproduction Steps

For a defect, provide repeatable steps.

1. Sign in.
2. Allow the access token to expire.
3. Perform an API operation.
4. Observe the failure.

For a feature, this section may instead describe the user workflow.

## Evidence

List the supporting files stored in this folder.

- Browser console log: `evidence/browser-console.txt`
- Server log: `evidence/server.log`
- Screenshot: `evidence/error.png`

## Analysis

Record the investigation, suspected cause, technical constraints, and relevant client/server interactions.

When investigating Ledger defects, consider both:

- Angular browser console and network activity
- Java server logs and API behaviour

## Scope

### Ledger Client

List expected changes to the Angular client.

### Ledger Server

List expected changes to the Java server.

### Database

List any PostgreSQL, JPA, Flyway, or data migration changes.

### Deployment and Operations

List any Docker, Docker Compose, Jenkins, Ansible, script, backup, restore, or smoke-test changes.

### Documentation

Check whether the following require updates:

- `ledger-docs/DATA_MODEL.md`
- `ledger-docs/ARCHITECTURE.md`
- `ledger-docs/BILLING_RULES.md`
- other user or deployment documentation

## Implementation Steps

- [ ] Reproduce or define the required behaviour.
- [ ] Add or update automated tests.
- [ ] Implement the server changes.
- [ ] Implement the client changes.
- [ ] Update database migrations if required.
- [ ] Update deployment or operational scripts if required.
- [ ] Update documentation.
- [ ] Run server tests.
- [ ] Run client tests.
- [ ] Run integration or smoke tests.
- [ ] Record the final Git references.
- [ ] Complete the completion summary.

## Acceptance Criteria

- [ ] The required behaviour is clearly defined.
- [ ] The original defect can no longer be reproduced, or the feature works as specified.
- [ ] Client and server behaviour remain consistent.
- [ ] Automated tests cover the important behaviour.
- [ ] Database definitions and migrations are consistent.
- [ ] Relevant documentation has been updated.
- [ ] Deployment and rollback implications have been checked.
- [ ] The change has been verified in the appropriate Ledger environments.

## Test Evidence

Record the tests performed and their results.

### Server Tests

```text
Command:
Result:
```

### Client Tests

```text
Command:
Result:
```

### Smoke Test

```text
Environment:
Command:
Result:
```

### Manual Verification

Describe any manual checks performed.

## Git References

Record all relevant repositories because Ledger changes may span several projects.

### Top-Level Ledger Repository

- Branch:
- Commits:
- Pull request:

### Ledger Client

- Branch:
- Commits:
- Pull request:

### Ledger Server

- Branch:
- Commits:
- Pull request:

### Ledger Docs

- Branch:
- Commits:
- Pull request:

## Deployment and Rollback Notes

Describe:

- deployment steps
- configuration changes
- database migration implications
- compatibility considerations
- rollback procedure

## Completion Summary

Complete this section when the item is finished.

Summarise:

- what changed
- why the chosen solution was used
- any important limitations
- tests performed
- deployment outcome
- follow-up work, if any

## Completed Date

YYYY-MM-DD
```

## Change Register

The top-level `INDEX.md` should provide a compact view of all changes.

Example:

```markdown
# Ledger Change Register

| ID | Type | Description | Priority | Status | Opened | Completed |
|---|---|---|---|---|---|---|
| DEF-0001 | Defect | Login fails after token expiry | High | In progress | 2026-07-15 | |
| FEAT-0002 | Feature | Add customer search | Medium | To do | 2026-07-15 | |
| CHG-0003 | Change | Improve deployment backup process | Medium | Completed | 2026-07-10 | 2026-07-14 |
```

The index should be updated whenever:

- a new change is created
- a change starts
- priority changes
- a change is completed
- a change is cancelled or superseded

## Workflow

### 1. Create the Change

Create a new folder under `todo`.

Example:

```text
change-control/todo/DEF-0004-invoice-rounding-error/
```

Add the item `README.md` and any available evidence.

Add the item to `INDEX.md`.

### 2. Define the Change

Before implementation, record:

- the problem or requirement
- expected behaviour
- scope
- implementation steps
- acceptance criteria
- known risks
- affected Ledger repositories

### 3. Start Work

Move the complete folder from `todo` to `in-progress`.

Update:

- the status in the item `README.md`
- the status in `INDEX.md`
- the Git branch references

Example branch names:

```text
defect/DEF-0001-token-expiry
feature/FEAT-0002-customer-search
change/CHG-0003-backup-process
```

### 4. Implement and Verify

Work through the implementation checklist.

For Ledger changes, consider all relevant areas:

- Angular client
- Java server
- PostgreSQL and JPA
- Docker and Docker Compose
- Jenkins
- Ansible
- remote scripts
- smoke tests
- Ledger documentation

Where a defect crosses the HTTP boundary, preserve evidence from both the browser and server.

### 5. Complete the Change

Before marking the item complete:

- confirm the acceptance criteria
- record tests and results
- record Git commits and pull requests
- document deployment and rollback implications
- complete the completion summary
- add the completed date

Move the whole folder to `completed`.

Update `INDEX.md`.

## Git and Repository Considerations

Ledger consists of a top-level repository and several submodules. A single change may therefore involve commits in:

- `ledger`
- `ledger-client`
- `ledger-server`
- `ledger-docs`

The change record should link all relevant commits and branches.

The detailed change record should normally remain in one place rather than being split between client and server repositories. This preserves the full end-to-end context.

## Documentation and Data-Model Consistency

When a change affects the data model or billing behaviour, verify that the implementation remains consistent with:

- PostgreSQL schema and migrations
- JPA entity definitions
- API request and response models
- Angular client models
- `DATA_MODEL.md`
- `ARCHITECTURE.md`
- `BILLING_RULES.md`

A change should not be considered complete while these definitions disagree.

## File-Based System Versus GitHub Issues

A file-based change-control system has several advantages:

- it is simple
- it is version-controlled
- it remains available offline
- it supports detailed evidence and implementation notes
- it is easy to archive permanently
- it is not tied to a particular issue-tracking service

Its main limitations are:

- limited filtering and searching
- no automatic notifications
- no built-in comments or assignment workflow
- less direct integration with pull requests
- manual maintenance of the index and status folders

A hybrid approach can be introduced later:

- use a GitHub Issue for discussion, labels, and pull-request integration
- use the change-control folder for the detailed investigation, evidence, implementation plan, test results, and completion record

For a single-developer project, the file-based approach is a reasonable starting point.

## Principles

Every change should have:

- a stable identifier
- a clear description
- defined scope
- implementation steps
- acceptance criteria
- supporting evidence
- test results
- Git references
- deployment and rollback notes
- a completion summary

The purpose of the system is not to add unnecessary process. It is to ensure that each Ledger change can be understood, implemented, tested, deployed, reviewed, and traced later.
