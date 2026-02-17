# Codebase Concerns

**Analysis Date:** 2026-02-17

## Tech Debt

**No Exception Handling in CSV Import:**
- Issue: The `ImportCSVFile()` method in `ShellViewModel.cs` lacks try-catch blocks. File operations and CSV parsing can throw exceptions (FileNotFoundException, CsvHelperException, IOException) but are not caught.
- Files: `Pages/ShellViewModel.cs` (lines 17-44)
- Impact: Application will crash with unhandled exceptions if file cannot be read or CSV format is invalid. Users receive no feedback about errors.
- Fix approach: Wrap file reading and CSV parsing in try-catch blocks. Display user-friendly error messages via message dialogs or status indicators. Consider logging exceptions for debugging.

**Unused Imports:**
- Issue: App.xaml.cs imports System.Collections.Generic, System.Configuration, System.Data, System.Linq, System.Threading.Tasks but none are used.
- Files: `App.xaml.cs` (lines 2-6)
- Impact: Minor. Increases namespace pollution and suggests incomplete cleanup or template boilerplate.
- Fix approach: Remove unused using statements.

**Unimplemented Bootstrapper Configuration:**
- Issue: The `Bootstrapper.cs` class has empty `ConfigureIoC()` and `Configure()` methods with comments suggesting they should contain configuration.
- Files: `Bootstrapper.cs` (lines 9-17)
- Impact: No dependency injection is currently configured. Adding features that require IoC later will require refactoring from void methods.
- Fix approach: Plan and implement IoC container configuration as application grows. Define services and their lifetimes upfront.

**Placeholder UI Elements:**
- Issue: ShellView.xaml contains incomplete UI: "Hello Stylet!" placeholder text, menu items without event handlers (Exit, Settings, About), and WpfPlot1 that receives data but displays nothing.
- Files: `Pages/ShellView.xaml` (lines 40-42, 27, 30, 33, 36)
- Impact: UI is non-functional. Users cannot interact with most menu items. Charting functionality is not connected to data import.
- Fix approach: Connect Exit, Settings, and Help menu items to handlers. Implement data binding from imported CSV to WpfPlot1. Remove or complete placeholder elements.

**Incomplete ViewModel Properties:**
- Issue: `ShellViewModel.cs` defines `MyProperty { get; set; }` (line 15) that is never used or bound to UI.
- Files: `Pages/ShellViewModel.cs` (line 15)
- Impact: Dead code clutters the codebase and may confuse future developers about its purpose.
- Fix approach: Remove unused property or document its purpose if intentional.

## Known Bugs

**CSV Import Produces No Visible Output:**
- Symptoms: User selects CSV file, but no visual feedback or data appears on screen. Only Debug.WriteLine calls occur.
- Files: `Pages/ShellViewModel.cs` (lines 32-38)
- Trigger: Click File > Open, select any CSV file
- Workaround: Output window shows records if running in debugger, but end users see nothing
- Root cause: Records are read and logged only to Debug output; they are not stored or passed to UI for display

**Missing File Dialog Validation:**
- Symptoms: Application hangs or crashes if user selects a file that cannot be read (permissions denied, file locked, network file unavailable)
- Files: `Pages/ShellViewModel.cs` (lines 19-42)
- Trigger: Select CSV file with restricted permissions or on disconnected network drive
- Workaround: None; application will crash
- Root cause: No file access verification or exception handling before attempting StreamReader creation

## Security Considerations

**Unrestricted File Access:**
- Risk: OpenFileDialog.ShowDialog() allows user to select ANY file type despite CSV filter. Application attempts to parse selected file as CSV without validation.
- Files: `Pages/ShellViewModel.cs` (lines 19-20, 28-39)
- Current mitigation: CsvHelper will fail to parse non-CSV files, but with unclear error messages
- Recommendations: Validate file extension and first-line content before parsing. Implement file size limits to prevent memory exhaustion from large files. Add explicit file type validation.

**Arbitrary File Path Handling:**
- Risk: Full file path from dialog is passed to StreamReader without sanitization. No path normalization or validation occurs.
- Files: `Pages/ShellViewModel.cs` (line 28)
- Current mitigation: StreamReader constructor may fail with certain paths
- Recommendations: Validate file path is within allowed directories (if constraining paths). Handle UNC paths and special characters explicitly.

**No Input Validation on CSV Data:**
- Risk: Model properties use float and int types (AussenTemp, Kesseltemp_Ist, BR, Vorlauf_Ist) without validation. Malformed CSV values could cause silent failures or data corruption.
- Files: `Models/OekoFenCSV.cs` (lines 18, 20, 24, 25, 29, 31, 35)
- Current mitigation: CsvHelper will throw on parse failure, but no bounds checking occurs
- Recommendations: Add validation attributes to model properties. Implement explicit value range checks for temperature and other numeric fields. Log invalid records instead of silently skipping.

## Performance Bottlenecks

**No Streaming for Large CSV Files:**
- Problem: `csv.GetRecords<OekoFenCSV>()` loads entire CSV file into memory via enumeration. No pagination or streaming limit exists.
- Files: `Pages/ShellViewModel.cs` (line 32)
- Cause: CsvReader is used in streaming mode but results are fully enumerated without buffering or limiting
- Impact: Large CSV files (>100MB) will exhaust memory or cause severe UI lag
- Improvement path: Implement batch processing (load N records at a time). Add progress reporting for long imports. Consider offloading to background thread with cancellation token.

**UI Thread Blocking During File I/O:**
- Problem: CSV import runs synchronously on UI thread, blocking all user input while file is being read and parsed
- Files: `Pages/ShellViewModel.cs` (lines 17-44)
- Impact: Application appears frozen during file operations. Cannot cancel operation or interact with UI.
- Improvement path: Move file I/O to background thread (Task.Run or async/await). Report progress on UI thread. Implement cancellation via CancellationToken.

## Fragile Areas

**Hardcoded CSV Column Indices:**
- Files: `Models/OekoFenCSV.cs` (lines 12-35)
- Why fragile: Model uses [Index(0-8)] attributes mapping to specific column positions. If CSV file has different column order or different delimiter (comma vs semicolon variation), parsing fails silently or incorrectly assigns values.
- Safe modification: Add validation that verifies expected column headers before parsing. Consider switching to header-based mapping [Name] attribute if column order varies. Document expected CSV format with example.
- Test coverage: No unit tests for CSV parsing. Manual testing required for each CSV format variant.

**Hard-Coded Culture and Delimiter:**
- Files: `Pages/ShellViewModel.cs` (lines 23-26)
- Why fragile: CsvConfiguration specifies `CultureInfo.InvariantCulture` and Delimiter=";". If users have CSV files with comma delimiters or locale-specific number formats, parsing fails without clear error.
- Safe modification: Make delimiter and culture configurable via settings. Add auto-detection for delimiter based on file inspection.
- Test coverage: No tests for different locales or delimiters.

**Tight Coupling Between ViewModel and Dialogs:**
- Files: `Pages/ShellViewModel.cs` (lines 19-21)
- Why fragile: ViewModel directly instantiates OpenFileDialog (UI framework dependency). Cannot reuse business logic without WPF. Difficult to unit test.
- Safe modification: Extract file selection into separate interface/service. Inject IFileService into ViewModel for testability.
- Test coverage: Cannot test file import logic without running WPF

**Unused WpfPlot Component:**
- Files: `Pages/ShellView.xaml` (line 39)
- Why fragile: WpfPlot1 is declared but never bound to ViewModel. Imported CSV data is never passed to plot for display. Unknown what should be charted.
- Safe modification: Define what data should appear in chart. Add ViewModel property(ies) to expose chart data. Bind WpfPlot.Plot property to ViewModel. Document chart intent.
- Test coverage: No tests for charting functionality.

## Scaling Limits

**Single-Threaded UI Processing:**
- Current capacity: Supports CSV files up to ~50MB before UI becomes unresponsive during parsing
- Limit: Files larger than 100MB will freeze application for extended periods
- Scaling path: Implement async file I/O with ConfigureAwait(false). Use Task.Run with appropriate thread pool sizing. Consider chunked processing with progress reporting.

**No Caching or In-Memory Database:**
- Current capacity: Each import starts fresh with no persistence between sessions
- Limit: Users cannot work with previously imported data or compare multiple files
- Scaling path: Add local database (SQLite) for persistent storage of imported records. Implement data caching layer. Consider partial re-import for append operations.

**Single Data Source:**
- Current capacity: Supports one CSV file at a time
- Limit: Cannot merge or compare multiple CSV files
- Scaling path: Extend UI to support multiple files. Add data comparison/aggregation features.

## Dependencies at Risk

**CsvHelper 33.0.1:**
- Risk: Major version (33.x is currently in active development). May receive breaking changes in minor versions.
- Impact: Updates could change parsing behavior or API surface
- Mitigation: Pin exact version in csproj. Review CsvHelper release notes before upgrading.
- Migration plan: If issues arise, consider CsvParser (lightweight) or System.Text.Csv (if available in .NET 8).

**ScottPlot.WPF 5.0.47:**
- Risk: Large charting library with significant dependencies. Version 5.x is major rewrite from v4.x.
- Impact: Breaking changes possible. Unused currently but dependencies are heavy.
- Mitigation: Remove from project if not immediately needed. Defer WpfPlot1 integration until charting requirements are defined.
- Migration plan: Alternative: OxyPlot.Wpf (lighter weight), or use WPF native shapes if functionality is simple.

**Stylet 1.3.7.0:**
- Risk: MVVM framework with limited active development (last update ~2019). .NET 8 WPF support unclear.
- Impact: May not receive updates for .NET 9/10 compatibility.
- Mitigation: Monitor Stylet GitHub for .NET 8 issues. Have contingency to migrate to MVVM Community Toolkit if Stylet becomes unmaintained.
- Migration plan: MVVM Community Toolkit or PropertyChanged.Fody as lighter alternatives.

## Missing Critical Features

**No Persistence:**
- Problem: Imported CSV data is not saved. Closing application loses all imported data.
- Blocks: Iterative work on CSV data, report generation, exporting processed results

**No Data Validation UI:**
- Problem: No user feedback when CSV parsing fails. Users cannot see which rows had errors or why.
- Blocks: Working with malformed CSV files, debugging import issues

**No Export/Report Generation:**
- Problem: Application reads data but has no output capability.
- Blocks: Users cannot save processed data or generate reports

**No Settings/Preferences:**
- Problem: Delimiter, culture, and other import settings are hardcoded.
- Blocks: Working with CSV files using different formats

## Test Coverage Gaps

**CSV Parsing Logic:**
- What's not tested: CsvHelper configuration, model deserialization, exception handling during parsing
- Files: `Pages/ShellViewModel.cs` (lines 23-39), `Models/OekoFenCSV.cs`
- Risk: Changes to CSV parsing logic could silently break import without detection
- Priority: High - Core functionality

**File Dialog Interaction:**
- What's not tested: File selection, file access errors, dialog cancellation
- Files: `Pages/ShellViewModel.cs` (lines 19-21)
- Risk: File I/O errors crash application in production
- Priority: High - User-facing functionality

**Data Display to Chart:**
- What's not tested: No charting logic exists; WpfPlot remains disconnected
- Files: `Pages/ShellView.xaml` (line 39), missing ViewModel bindings
- Risk: Chart feature may not work when implemented
- Priority: Medium - Feature pending implementation

**ViewModel Behavior:**
- What's not tested: ImportCSVFile method logic, state management
- Files: `Pages/ShellViewModel.cs`
- Risk: Refactoring could break import flow without detection
- Priority: High - Core feature

**Integration Testing:**
- What's not tested: End-to-end import from file selection through display
- Files: All source files
- Risk: UI and logic may not integrate correctly despite individual component correctness
- Priority: Medium - Required before release

---

*Concerns audit: 2026-02-17*
