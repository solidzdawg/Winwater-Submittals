# ITEM SEPARATOR SHEET

---

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                                                                             │
│                                                                             │
│                           WINWATER                                          │
│                        PROJECT SUBMITTAL                                    │
│                                                                             │
│                     ┌───────────────────────┐                              │
│                     │                       │                              │
│                     │    ITEM  {{ ITEM_NUM }}│                              │
│                     │                       │                              │
│                     └───────────────────────┘                              │
│                                                                             │
│                  {{ ITEM_DESCRIPTION }}                                     │
│                                                                             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Manufacturer:    {{ MANUFACTURER }}                                       │
│   Model / Part #:  {{ MODEL_NUMBER }}                                       │
│   Spec Section:    {{ SPEC_SECTION }}                                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Included in this section:                                                 │
│   ☐ Product Data / Cut Sheet                                                │
│   ☐ NSF 61 Certification                                                    │
│   ☐ NSF 372 (Lead-Free) Certification                                       │
│   ☐ UL / cUL Listing                                                        │
│   ☐ ASSE Certification                                                      │
│   ☐ Referenced Specification Pages                                          │
│   ☐ Other: _______________                                                  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Project: {{ PROJECT_NAME }}          Submittal #: {{ SUBMITTAL_NUMBER }} │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Instructions for Use

| Placeholder           | Description                                              |
|-----------------------|----------------------------------------------------------|
| `ITEM_NUM`            | Sequential item number (01, 02, 03 …)                    |
| `ITEM_DESCRIPTION`    | Plain-English product name (e.g., "Pressure Reducing Valve") |
| `MANUFACTURER`        | Manufacturer name (e.g., "Watts Water Technologies")     |
| `MODEL_NUMBER`        | Exact model / catalog number (e.g., "LF25AUB-Z3")       |
| `SPEC_SECTION`        | CSI section number (e.g., "22 05 23")                    |
| `PROJECT_NAME`        | Project name (e.g., "Double RR")                         |
| `SUBMITTAL_NUMBER`    | Full submittal number (e.g., "WW-2024-001")              |

Check the boxes that apply to documents included in this item section.
