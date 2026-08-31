# Graph Report - _bot_gamehub  (2026-08-31)

## Corpus Check
- 25 files · ~68,212 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 152 nodes · 274 edges · 15 communities (8 shown, 7 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9efd3092`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Database
- web_app.py
- ApiDownloader
- config.py
- PackageBuilder
- Graphify Pipeline
- setup_vps_ubuntu.sh
- Game Troubleshooting Guide Link
- GitHub and Cross-Repo Merge
- Media Transcription Pipeline
- VPS Runtime Architecture
- Python Runtime Dependency Stack
- Responsive Ticket Status Views
- EmailService

## God Nodes (most connected - your core abstractions)
1. `PackageBuilder` - 20 edges
2. `Database` - 18 edges
3. `TicketService` - 17 edges
4. `ApiDownloader` - 13 edges
5. `EmailService` - 11 edges
6. `TicketRow` - 10 edges
7. `ApiSource` - 9 edges
8. `ApiRegistry` - 9 edges
9. `Settings` - 9 edges
10. `admin_create_ticket()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `GameHub Admin Dashboard` --conceptually_related_to--> `admin_dashboard()`  [INFERRED]
  templates/dashboard.html → web_app.py
- `GameHub Admin Login` --references--> `admin_login()`  [EXTRACTED]
  templates/login.html → web_app.py
- `Ticket Build Form` --references--> `admin_create_ticket()`  [EXTRACTED]
  templates/dashboard.html → web_app.py
- `PackageBuilder` --uses--> `ApiDownloader`  [INFERRED]
  builder.py → api_downloader.py
- `PackageBuilder` --uses--> `ApiRegistry`  [INFERRED]
  builder.py → api_registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graphify Build and Navigation** — claude_skills_graphify_skill_graphify_pipeline, claude_skills_graphify_references_extraction_spec_extraction_contract, claude_skills_graphify_references_query_graph_traversal, claude_skills_graphify_references_update_incremental_graph_update [EXTRACTED 1.00]
- **GameHub Ticket Delivery Flow** — templates_dashboard_ticket_build_form, web_app_admin_create_ticket, ticket_service_ticketservice_create_ticket, builder_packagebuilder_build_ticket_package, email_service_emailservice_send_ticket_email [INFERRED 0.95]

## Communities (15 total, 7 thin omitted)

### Community 0 - "Database"
Cohesion: 0.10
Nodes (8): BuildResult, Database, TicketRow, datetime, 24-Hour File Message Deletion, Ticket Redeem Flow, TicketCreateResult, TicketService

### Community 1 - "web_app.py"
Cohesion: 0.13
Nodes (28): get, message, on_event, post, Admin and Telegram Endpoints, RedirectResponse, Request, GameHub Admin Dashboard (+20 more)

### Community 2 - "ApiDownloader"
Cohesion: 0.16
Nodes (9): ApiDownloader, DownloadError, Exception, Path, ApiRegistry, ApiSource, Path, API Selection Modes (+1 more)

### Community 3 - "config.py"
Cohesion: 0.36
Nodes (7): _choose_addgame_file(), _choose_bypass_template(), ensure_directories(), load_settings(), _parse_admin_ids(), Path, Settings

### Community 4 - "PackageBuilder"
Cohesion: 0.27
Nodes (4): BuildError, PackageBuilder, Exception, Path

### Community 5 - "Graphify Pipeline"
Cohesion: 0.22
Nodes (9): Graphify Skill Trigger, Graphify Knowledge Graph Rules, Incremental URL and Watch Ingestion, Graph Export Formats, Semantic Extraction Contract, Graph Update Hooks, Graph Query Traversal, Incremental Graph Update (+1 more)

### Community 14 - "EmailService"
Cohesion: 0.12
Nodes (7): EmailService, FakeDownloader, FakeRegistry, FakeSMTP, PackageRebrandingTests, Path, RebrandingTests

## Knowledge Gaps
- **18 isolated node(s):** `setup_vps_ubuntu.sh script`, `24-Hour File Message Deletion`, `30-Day Admin Session`, `GameHub Favicon`, `Media Transcription Pipeline` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PackageBuilder` connect `PackageBuilder` to `Database`, `web_app.py`, `ApiDownloader`, `config.py`, `EmailService`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Why does `TicketService` connect `Database` to `web_app.py`, `PackageBuilder`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `web_app.py`, `PackageBuilder`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `PackageBuilder` (e.g. with `ApiDownloader` and `ApiRegistry`) actually correct?**
  _`PackageBuilder` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TicketService` (e.g. with `BuildResult` and `PackageBuilder`) actually correct?**
  _`TicketService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ApiDownloader` (e.g. with `ApiSource` and `PackageBuilder`) actually correct?**
  _`ApiDownloader` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `EmailService` (e.g. with `Settings` and `RebrandingTests`) actually correct?**
  _`EmailService` has 2 INFERRED edges - model-reasoned connections that need verification._