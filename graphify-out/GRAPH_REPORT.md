# Graph Report - rasp  (2026-09-17)

## Corpus Check
- 36 files · ~432,395 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 448 nodes · 609 edges · 35 communities (21 shown, 14 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]

## God Nodes (most connected - your core abstractions)
1. `tokenKinds` - 147 edges
2. `Connection` - 23 edges
3. `VideoRTC` - 22 edges
4. `Request` - 21 edges
5. `BudgetDbTest` - 14 edges
6. `flash()` - 12 edges
7. `parse_money()` - 12 edges
8. `page()` - 11 edges
9. `Decimal` - 11 edges
10. `VideoStream` - 9 edges

## Surprising Connections (you probably didn't know these)
- `parse_rate()` --calls--> `Decimal`  [INFERRED]
  apps/budget/app.py → apps/budget/fx.py
- `api_ten()` --calls--> `ten_percent()`  [INFERRED]
  apps/budget/app.py → apps/budget/money.py
- `field_money()` --calls--> `Decimal`  [INFERRED]
  apps/budget/money.py → apps/budget/fx.py
- `format_money()` --calls--> `Decimal`  [INFERRED]
  apps/budget/money.py → apps/budget/fx.py
- `parse_money()` --calls--> `Decimal`  [INFERRED]
  apps/budget/money.py → apps/budget/fx.py

## Import Cycles
- 1-file cycle: `apps/budget/fx.py -> apps/budget/fx.py`

## Communities (35 total, 14 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.20
Nodes (9): Camera viewer (browser), Config, Family budget, How it is wired, Install on the Pi, Raspberry Pi local apps, Troubleshooting, Verified (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (30): Any, add_expense(), add_fx(), add_income(), add_sleeve_deposit(), balances(), connect(), excluded_accounts() (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (32): account_of(), api_ten(), counted_totals(), ctx(), exclude_toggle(), expense_edit(), expense_form(), expense_save() (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.01
Nodes (147): --blur-lg, --blur-md, --blur-sm, --border-dark, --border-gold, --border-subtle, --color-accent-primary, --color-accent-sea (+139 more)

### Community 12 - "Community 12"
Cohesion: 0.28
Nodes (10): Any, _from_cbr(), _from_erapi(), _get(), usd_cents_to_rub_cents(), usd_to_rub(), field_money(), format_money() (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (40): boot(), collectProps(), compileAttr(), compileTemplate(), createComponentFactory(), createExternalModules(), createHelmetManager(), createPseudoSheet() (+32 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (21): Backgrounds, Color System, CONTENT FUNDAMENTALS, Content Style Modes, Copywriting patterns, Core Services, FILE INDEX, Glass Effect (+13 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (18): replaces, replaces, replaces, Badge, Button, Card, Tag, overrides (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (12): brandFonts, cards, components, fonts, globalCssPaths, hasThumbnailHtml, namespace, source (+4 more)

### Community 32 - "Community 32"
Cohesion: 0.67
Nodes (5): quiet-hours.sh script, enter_quiet(), in_quiet_window(), leave_quiet(), set_display()

### Community 34 - "Community 34"
Cohesion: 0.48
Nodes (5): camera_ok(), restart_go2rtc(), wait_for_api(), write_status(), watch-camera.sh script

## Knowledge Gaps
- **203 isolated node(s):** `plugins`, `react/forbid-elements`, `no-restricted-imports`, `no-restricted-syntax`, `overrides` (+198 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `tokenKinds` connect `Community 7` to `Community 16`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `x-omelette` connect `Community 16` to `Community 7`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `BudgetDbTest` connect `Community 3` to `Community 12`, `Community 5`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **What connects `plugins`, `react/forbid-elements`, `no-restricted-imports` to the rest of the system?**
  _204 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.09879032258064516 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.1408199643493761 - nodes in this community are weakly interconnected._
- **Should `Community 7` be split into smaller, more focused modules?**
  _Cohesion score 0.013605442176870748 - nodes in this community are weakly interconnected._