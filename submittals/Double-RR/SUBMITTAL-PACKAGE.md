# Double RR — Submittal Package

**Submittal No.:** WW-2024-001
**Project:** Double RR
**Status:** In Progress

---

## Equipment Schedule (10 Items)

| # | Description | Manufacturer | Model | Spec Section | Status |
|---|-------------|-------------|-------|-------------|--------|
| 1 | 2" Pressure Reducing Valve | Watts | LF25AUB-Z3 | 22 05 23 | ⚠️ Docs needed |
| 2 | 2.5" Double Check Valve Assembly | Watts | 007M3QT | 22 05 23 | ⚠️ Docs needed |
| 3 | 2" Bronze Gate Valve | Nibco | T-113 | 22 05 23 | ⚠️ Docs needed |
| 4 | 1.5" Bronze Gate Valve | Nibco | T-113 | 22 05 23 | ⚠️ Docs needed |
| 5 | 0.75" Full Port Ball Valve | Apollo | 77-100 | 22 05 23 | ⚠️ Docs needed |
| 6 | 1.5" Y-Strainer | Mueller | 351 | 22 05 23 | ⚠️ Docs needed |
| 7 | 3" Cold Water Meter | Sensus | iPERL | 22 05 11 | ⚠️ Docs needed |
| 8 | 50-Gal Expansion Tank | Amtrol | ST-30 | 22 05 23 | ⚠️ Docs needed |
| 9 | 1.5 HP Circulating Pump | Grundfos | UP26-96F | 23 21 23 | ⚠️ Docs needed |
| 10 | 100-Gal Commercial Water Heater | AO Smith | BTH-199A | 22 33 00 | ⚠️ Docs needed |

---

## Assembly Checklist

- [ ] manifest.csv populated with all items
- [ ] Docs cached from Z: drive (`python scripts/browse-docs.py --cache`)
- [ ] Agent run (`python scripts/agent.py --project "Double-RR"`)
- [ ] Agent log reviewed — missing docs attached manually
- [ ] Quality check complete (see `docs/assembly-guide.md`)
- [ ] Final PDF transmitted to GC

---

## Run the Agent

```bash
# One command builds the entire package:
python scripts/agent.py --project "Double-RR"

# Preview without writing files:
python scripts/agent.py --project "Double-RR" --dry-run
```

After the agent runs, review `agent-run.log` in this folder.
