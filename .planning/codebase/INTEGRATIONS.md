# External Integrations

**Analysis Date:** 2026-02-17

## APIs & External Services

**Not Applicable:**
- No external APIs currently integrated
- Application is standalone desktop utility

## Data Storage

**Databases:**
- None - Application does not use persistent database

**File Storage:**
- Local filesystem only
  - CSV import: User selects files via OpenFileDialog (`Pages/ShellViewModel.cs` line 19-20)
  - CSV format: Semicolon-delimited (`;` delimiter, see `ShellViewModel.cs` line 26)
  - Sample files: `Files/touch_20260216.csv` (377KB)

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- None - Standalone desktop application with no user authentication

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Debug output only via `Debug.WriteLine()` in `Pages/ShellViewModel.cs` line 37

## CI/CD & Deployment

**Hosting:**
- None - Standalone Windows desktop application

**CI Pipeline:**
- None detected

**Build Output:**
- Local compilation to executable (bin directory)

## Environment Configuration

**Required env vars:**
- None

**Secrets location:**
- No secrets management - application is standalone

## Data Import/Export

**Incoming:**
- CSV file import via file dialog
  - Model: `OekoFenCSV` in `Models/OekoFenCSV.cs`
  - Supports fields: Datum, Zeit, AussenTemp, AussenTempTakt, Kesseltemp_Ist, Kesseltemp_Soll, BR, Sperrzeit, Vorlauf_Ist
  - CSV configuration: CultureInfo.InvariantCulture, semicolon delimiter, lowercase header matching

**Outgoing:**
- None - Data is displayed in UI via ScottPlot visualization, not exported

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Data Format Specifications

**CSV Input:**
- Delimiter: Semicolon (`;`)
- Header Matching: Case-insensitive (converted to lowercase, see `ShellViewModel.cs` line 25)
- Culture: Invariant (numeric parsing uses invariant culture)
- Encoding: Default system encoding from StreamReader

---

*Integration audit: 2026-02-17*
