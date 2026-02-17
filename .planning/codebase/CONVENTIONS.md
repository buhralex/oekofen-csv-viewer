# Coding Conventions

**Analysis Date:** 2026-02-17

## Naming Patterns

**Files:**
- PascalCase for all C# files (e.g., `App.xaml.cs`, `ShellViewModel.cs`, `OekoFenCSV.cs`)
- Files match class name exactly
- XAML files paired with .xaml.cs code-behind files

**Namespaces:**
- Root namespace: `OekoFEN_CSV_Viewer`
- Feature-based organization: `OekoFEN_CSV_Viewer.Models`, `OekoFEN_CSV_Viewer.Pages`
- Namespace hierarchy matches directory structure

**Classes and Types:**
- PascalCase for all class names: `App`, `Bootstrapper`, `ShellViewModel`, `ShellView`
- Data model classes: PascalCase (e.g., `OekoFenCSV`)
- Partial classes used for XAML code-behind: `public partial class ShellView : Window`

**Properties:**
- PascalCase for all public properties: `Datum`, `Zeit`, `AussenTemp`, `Kesseltemp_Ist`, `MyProperty`
- Auto-properties used: `{ get; set; }`
- Mixed naming convention observed: Properties like `Kesseltemp_Ist`, `Kesseltemp_Soll` use underscores (domain-specific German terminology preserved)

**Methods:**
- PascalCase for public methods: `ImportCSVFile()`, `ConfigureIoC()`, `Configure()`
- Action methods (bound to UI commands) are public: `public void ImportCSVFile()`
- Protected override methods in base class hierarchies: `protected override void ConfigureIoC(...)`

**Variables:**
- Local variables use camelCase: `openFileDialog`, `config`, `reader`, `csv`, `records`, `record`
- Loop variables are descriptive

## Code Style

**Formatting:**
- No explicit formatter detected (EditorConfig or .editorconfig absent)
- 4-space indentation observed consistently
- Brace style: C# convention (opening brace on same line for methods/classes)
- Line length: No strict limit observed

**Linting:**
- No StyleCop or Roslyn analyzer configuration detected
- No .editorconfig file present
- Code follows C# naming conventions without enforced rules

**Accessibility Modifiers:**
- Explicit access modifiers always used: `public`, `protected`, `private` declared explicitly
- No implicit internal defaults
- Override keyword used properly: `protected override`

## Import Organization

**Order:**
1. External third-party packages: `CsvHelper`, `CsvHelper.Configuration`, `Microsoft.Win32`, `Stylet`, `StyletIoC`
2. System namespaces: `System`, `System.Collections.Generic`, `System.Configuration`, `System.Data`, `System.Diagnostics`, `System.Globalization`, `System.IO`, `System.Linq`, `System.Text`, `System.Threading.Tasks`, `System.Windows`
3. Application-specific namespaces: `OekoFEN_CSV_Viewer.Models`, `OekoFEN_CSV_Viewer.Pages`

**Pattern:**
- External packages grouped at top
- System namespaces next
- Local project imports last
- Unused imports occasionally present (e.g., `System.Collections.Generic` and `System.Text` in `OekoFenCSV.cs` are unused)

## Error Handling

**Strategy:** Minimal explicit error handling observed.

**Patterns:**
- No try-catch blocks in current codebase
- `using` statements for resource management: File operations wrapped in nested `using` statements for `StreamReader` and `CsvReader`
- File dialog returns checked with equality: `if (openFileDialog.ShowDialog() == true)`
- Error handling deferred to runtime (file not found, parsing errors not caught)

## Logging

**Framework:** No logging framework configured. Console debugging used via `System.Diagnostics.Debug`.

**Patterns:**
- `Debug.WriteLine(record.ToString())` in `ShellViewModel.ImportCSVFile()` for diagnostics
- Output goes to Debug console only, not production logs
- No structured logging

## Comments

**When to Comment:**
- Minimal comments in production code
- XML documentation comments used for class-level documentation
- Method-level comments present on auto-generated or framework code

**Documentation:**
- XML doc comments on generated App.xaml.cs: `/// <summary>Interaction logic for App.xaml</summary>`
- Similar pattern in ShellView.xaml.cs
- Sparse in business logic (ShellViewModel has no method documentation)

**TODO/FIXME:**
- No TODO, FIXME, HACK, or XXX comments present in source code
- Commented-out code present: `//var records = csv.GetRecords<dynamic>();` in ShellViewModel

## Function Design

**Size:** Small to medium. Largest method is `ImportCSVFile()` at 27 lines of actual logic.

**Parameters:**
- Methods take no parameters (UI-driven commands): `public void ImportCSVFile()`
- Dialog result handling through local variables, not parameter passing
- Configuration objects created locally within methods

**Return Values:**
- Void return type used for UI command handlers: `public void ImportCSVFile()`
- No return value validation
- Async operations not used despite `System.Threading.Tasks` imports

## Module Design

**Separation of Concerns:**
- Models layer: `OekoFEN_CSV_Viewer.Models` - Data model class `OekoFenCSV` with attribute-based CSV mapping
- View layer: `OekoFEN_CSV_Viewer.Pages` - XAML UI and code-behind
- ViewModel layer: `OekoFEN_CSV_Viewer.Pages` - `ShellViewModel` containing business logic
- Bootstrap/DI: `Bootstrapper.cs` handles IoC configuration

**Exports:**
- All classes are public and exportable
- No internal sealing observed
- Partial classes used to separate XAML-generated code from custom code-behind

**Barrel Files:**
- Not applicable for this C# WPF application

## Property Patterns

**Auto-Properties:**
- Exclusively used in data models: `public string Datum { get; set; }`
- Properties exposed directly without backing fields
- No property validation or change notification (except in ViewModels via Stylet framework)

**Stylet Framework Integration:**
- `ShellViewModel : Screen` - Base class from Stylet MVVM framework
- Properties should use framework patterns for property change notification
- Current `MyProperty` usage suggests incomplete property implementation

## Attributes

**CsvHelper Attributes:**
- Index-based column mapping: `[Index(0)]`, `[Index(1)]`, etc. in `OekoFenCSV` model
- Maps CSV columns by position to properties

**XAML Attributes:**
- Data context binding: `d:DataContext="{d:DesignInstance local:ShellViewModel}"`
- Command binding: `Command="{s:Action ImportCSVFile}"`
- Namespace declarations: `xmlns:s="https://github.com/canton7/Stylet"`

---

*Convention analysis: 2026-02-17*
