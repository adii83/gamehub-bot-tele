# Graph Report - _bot_gamehub  (2026-08-31)

## Corpus Check
- 26 files · ~68,535 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 157 nodes · 276 edges · 15 communities (9 shown, 6 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `51b1c621`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Database
- .test_ticket_package_uses_nexaplay_filename
- web_app.py
- ApiDownloader
- NexaPlay Admin Dashboard
- EmailService
- PackageBuilder
- Graphify Pipeline
- setup_vps_ubuntu.sh
- Game Troubleshooting Guide Link
- GitHub and Cross-Repo Merge
- Media Transcription Pipeline
- Python Runtime Dependency Stack
- NEXAPLAY Logo

## God Nodes (most connected - your core abstractions)
1. `PackageBuilder` - 20 edges
2. `Database` - 18 edges
3. `TicketService` - 17 edges
4. `ApiDownloader` - 13 edges
5. `EmailService` - 12 edges
6. `TicketRow` - 10 edges
7. `ApiSource` - 9 edges
8. `ApiRegistry` - 9 edges
9. `Settings` - 9 edges
10. `load_settings()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `PackageBuilder` --uses--> `ApiDownloader`  [INFERRED]
  builder.py → api_downloader.py
- `PackageBuilder` --uses--> `ApiRegistry`  [INFERRED]
  builder.py → api_registry.py
- `PackageBuilder` --uses--> `Settings`  [INFERRED]
  builder.py → config.py
- `PackageRebrandingTests` --uses--> `PackageBuilder`  [INFERRED]
  test_rebranding.py → builder.py
- `TicketService` --uses--> `PackageBuilder`  [INFERRED]
  ticket_service.py → builder.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build and Navigation** — claude_skills_graphify_skill_graphify_pipeline, claude_skills_graphify_references_extraction_spec_extraction_contract, claude_skills_graphify_references_query_graph_traversal, claude_skills_graphify_references_update_incremental_graph_update [EXTRACTED 1.00]
- **Ticket Build Configuration Flow** — templates_dashboard_ticket_build_form, templates_dashboard_api_selection, templates_dashboard_bypass_configuration, templates_dashboard_email_ticket_delivery [EXTRACTED 1.00]
- **Admin Login to Ticket Creation Flow** — templates_login_admin_credentials_form, templates_dashboard_nexaplay_admin_dashboard, templates_dashboard_ticket_build_form [INFERRED 0.95]

## Communities (15 total, 6 thin omitted)

### Community 0 - "Database"
Cohesion: 0.11
Nodes (6): BuildResult, Database, TicketRow, datetime, TicketCreateResult, TicketService

### Community 1 - ".test_ticket_package_uses_nexaplay_filename"
Cohesion: 0.29
Nodes (4): FakeDownloader, FakeRegistry, PackageRebrandingTests, Path

### Community 2 - "web_app.py"
Cohesion: 0.14
Nodes (23): get, message, on_event, post, RedirectResponse, Request, AdminEmailTests, admin_create_ticket() (+15 more)

### Community 3 - "ApiDownloader"
Cohesion: 0.18
Nodes (7): ApiDownloader, DownloadError, Exception, Path, ApiRegistry, ApiSource, Path

### Community 4 - "NexaPlay Admin Dashboard"
Cohesion: 0.14
Nodes (16): Admin Login Flow, Admin Web Panel, FastAPI Application, NexaPlay.zip Per-ticket Package, Telegram NexaPlay Bot VPS Mode, Ticket Redeem Flow, API Mode Selection, Build Process Summary (+8 more)

### Community 5 - "EmailService"
Cohesion: 0.17
Nodes (10): _choose_addgame_file(), _choose_bypass_template(), ensure_directories(), load_settings(), _parse_admin_ids(), Path, Settings, EmailService (+2 more)

### Community 6 - "PackageBuilder"
Cohesion: 0.27
Nodes (4): BuildError, PackageBuilder, Exception, Path

### Community 7 - "Graphify Pipeline"
Cohesion: 0.22
Nodes (9): Graphify Skill Trigger, Graphify Knowledge Graph Rules, Incremental URL and Watch Ingestion, Graph Export Formats, Semantic Extraction Contract, Graph Update Hooks, Graph Query Traversal, Incremental Graph Update (+1 more)

## Knowledge Gaps
- **20 isolated node(s):** `setup_vps_ubuntu.sh script`, `GitHub and Cross-Repo Merge`, `Media Transcription Pipeline`, `Python Runtime Dependency Stack`, `Graphify Skill Trigger` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PackageBuilder` connect `PackageBuilder` to `Database`, `.test_ticket_package_uses_nexaplay_filename`, `web_app.py`, `ApiDownloader`, `EmailService`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `TicketService` connect `Database` to `web_app.py`, `PackageBuilder`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `web_app.py`, `PackageBuilder`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `PackageBuilder` (e.g. with `ApiDownloader` and `ApiRegistry`) actually correct?**
  _`PackageBuilder` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TicketService` (e.g. with `BuildResult` and `PackageBuilder`) actually correct?**
  _`TicketService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ApiDownloader` (e.g. with `ApiSource` and `PackageBuilder`) actually correct?**
  _`ApiDownloader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `EmailService` (e.g. with `Settings` and `RebrandingTests`) actually correct?**
  _`EmailService` has 2 INFERRED edges - model-reasoned connections that need verification._