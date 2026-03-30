# SUBMITTAL COVER SHEET

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   WINWATER                                        [COMPANY LOGO]            │
│                                                                             │
│   PROJECT SUBMITTAL                                                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PROJECT NAME:     {{ PROJECT_NAME }}                                      │
│                                                                             │
│   PROJECT ADDRESS:  {{ PROJECT_ADDRESS }}                                   │
│                                                                             │
│   SUBMITTAL NO.:    {{ SUBMITTAL_NUMBER }}      REV.: {{ REVISION }}        │
│                                                                             │
│   SUBMITTAL TITLE:  {{ SUBMITTAL_TITLE }}                                   │
│                                                                             │
│   SPEC SECTION(S):  {{ SPEC_SECTIONS }}                                     │
│                                                                             │
│   DATE:             {{ SUBMITTAL_DATE }}                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   SUBMITTED BY                         SUBMITTED TO                        │
│   ─────────────────────────────────    ──────────────────────────────────  │
│   Company:  Winwater                   GC:  {{ GC_NAME }}                  │
│   PM:       {{ PM_NAME }}              EOR: {{ EOR_NAME }}                 │
│   Phone:    {{ PM_PHONE }}             Project #: {{ GC_PROJECT_NUMBER }}  │
│   Email:    {{ PM_EMAIL }}                                                 │
│                                                                             │
│   Signature: ________________________  Date: ___________________________   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   SUBMITTAL STATUS                                                          │
│   ☐ For Review     ☐ For Approval     ☐ For Construction     ☐ As-Built    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   REVISION HISTORY                                                          │
│   Rev  │ Date       │ Description of Change               │ By             │
│   ─────┼────────────┼─────────────────────────────────────┼─────────────── │
│   0    │            │ Original Issue                      │                │
│        │            │                                     │                │
│        │            │                                     │                │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CONTENTS SUMMARY                                                          │
│   This submittal contains {{ TOTAL_ITEMS }} items on {{ TOTAL_PAGES }} pages│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Instructions for Use

Replace all `{{ PLACEHOLDER }}` values with project-specific information:

| Placeholder           | Description                                              |
|-----------------------|----------------------------------------------------------|
| `PROJECT_NAME`        | Full project name (e.g., "Double RR")                    |
| `PROJECT_ADDRESS`     | Street address / location of project                     |
| `SUBMITTAL_NUMBER`    | WW-YYYY-### format (e.g., WW-2024-001)                   |
| `REVISION`            | Rev 0 for original; increment for resubmittals           |
| `SUBMITTAL_TITLE`     | Brief title (e.g., "Plumbing Equipment and Materials")   |
| `SPEC_SECTIONS`       | Comma-separated list (e.g., "22 05 00, 22 11 16")        |
| `SUBMITTAL_DATE`      | MM/DD/YYYY format                                        |
| `PM_NAME`             | Winwater project manager full name                       |
| `PM_PHONE`            | PM phone number                                          |
| `PM_EMAIL`            | PM email address                                         |
| `GC_NAME`             | General contractor company name                          |
| `EOR_NAME`            | Engineer of record (firm and contact)                    |
| `GC_PROJECT_NUMBER`   | GC's internal project or contract number                 |
| `TOTAL_ITEMS`         | Count of items in the submittal                          |
| `TOTAL_PAGES`         | Total page count of the package                          |
