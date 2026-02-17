# Testing Patterns

**Analysis Date:** 2026-02-17

## Test Framework

**Status:** No testing framework configured.

**Runner:**
- Not detected - No test project files (.csproj with Test SDK)
- No test dependencies in project file
- No test runner configuration (xunit, nunit, mstest)

**Assertion Library:**
- Not applicable - No testing infrastructure present

**Run Commands:**
- Not available - No test commands configured

## Test File Organization

**Status:** No test files exist in codebase.

**Location:**
- No dedicated `Tests` or `*.Tests` directory
- No `*.Test.cs` or `*.Spec.cs` files present
- No test projects in solution

**File Naming:**
- Not applicable - No test files to establish pattern

**Structure:**
- Not applicable - No test organization to document

## Testing Infrastructure Gap

**Current State:**
- Production project: `OekoFEN_CSV_Viewer.csproj` (net8.0-windows WPF application)
- No test project created
- Main assemblies in production: CsvHelper, ScottPlot.WPF, Stylet (all third-party)

**What Should Be Tested:**
The following areas lack automated test coverage and represent risk:

1. **CSV Import Logic** (`ShellViewModel.ImportCSVFile()`)
   - CSV parsing and mapping to `OekoFenCSV` model
   - File dialog interaction
   - Delimiter configuration (semicolon-delimited)
   - Culture-invariant parsing
   - No error handling for malformed CSV

2. **Data Model** (`OekoFenCSV.cs`)
   - Index-based CSV column mapping validation
   - Type conversion (float, int properties from string CSV data)
   - No validation attributes or constraints

3. **Bootstrapper** (`Bootstrapper.cs`)
   - IoC container configuration
   - View model and view registration
   - Currently has empty `ConfigureIoC()` method - no explicit DI setup

4. **ViewModel** (`ShellViewModel.cs`)
   - Property change notifications (inherits from Stylet's `Screen`)
   - Command execution and state management
   - Unused property `MyProperty` suggests incomplete implementation

## Recommended Testing Approach

**For a C# WPF Application:**

**Unit Testing Framework:**
```
Consider xUnit with xUnit.StaLib for WPF UI testing
Or: NUnit with NUnit.Extension.NUnit.Gui
Or: MSTest (built into Visual Studio)
```

**Test Project Structure:**
```
OekoFEN_CSV_Viewer/                    (main app)
OekoFEN_CSV_Viewer.Tests/              (unit tests)
├── Models/
│   └── OekoFenCSVTests.cs
├── Pages/
│   └── ShellViewModelTests.cs
├── Fixtures/
│   └── CsvTestData.cs
└── Integration/
    └── CsvImportIntegrationTests.cs
```

**Unit Test Pattern (Recommended):**
```csharp
[TestClass]
public class ShellViewModelTests
{
    private ShellViewModel viewModel;

    [TestInitialize]
    public void Setup()
    {
        viewModel = new ShellViewModel();
    }

    [TestMethod]
    public void ImportCSVFile_WithValidFile_ParsesRecordsCorrectly()
    {
        // Arrange
        var testFilePath = CreateTestCsvFile(new[] {
            "datum;zeit;aussentemp;...",
            "2026-02-17;14:00;15.5;..."
        });

        // Act
        viewModel.ImportCSVFile(testFilePath);

        // Assert
        Assert.AreEqual(1, viewModel.Records.Count);
        Assert.AreEqual("2026-02-17", viewModel.Records[0].Datum);
    }
}
```

**Mocking Strategy:**
- Mock `OpenFileDialog` to control test file paths
- Create test fixture CSV files in temp directory
- Mock Stylet Screen base class behavior if needed

**Test Data:**
```csharp
// Suggested fixture location: OekoFEN_CSV_Viewer.Tests/Fixtures/
public static class CsvTestData
{
    public static string ValidCsvContent =>
        @"Datum;Zeit;AussenTemp;AussenTempTakt;Kesseltemp_Ist;Kesseltemp_Soll;BR;Sperrzeit;Vorlauf_Ist
2026-02-17;14:00:00;15.5;0.0;60.2;65.0;1;0;45
2026-02-17;14:15:00;15.4;0.0;61.5;65.0;1;0;46";

    public static OekoFenCSV SampleRecord => new OekoFenCSV
    {
        Datum = "2026-02-17",
        Zeit = "14:00:00",
        AussenTemp = 15.5f,
        // ... other properties
    };
}
```

## Current Testing Limitations

**UI Testing:**
- WPF UI interactions (file dialogs, button clicks, menu selection) difficult to automate
- Stylet framework commands (`Command="{s:Action ImportCSVFile}"`) require ViewModel testing focus
- ScottPlot integration untestable without UI automation framework

**Integration Points Not Testable:**
- CsvHelper parsing with actual CSV files (requires file I/O)
- ScottPlot graph rendering (visualization component)
- File system operations (opening file dialogs)

## Coverage Goals

**Recommended Minimum Coverage:**
- Parsing logic: 100% (critical path)
- Data validation: 100% (prevents data corruption)
- ViewModel commands: 80%+ (UI-dependent)
- Overall: 70%+ target

**View Coverage Approach:**
- Focus on ViewModel logic, not View code-behind
- Use automated UI testing only for critical workflows
- Manual testing for graph visualization

## Test Execution

**When Testing Framework is Added:**

```bash
# Run all tests
dotnet test

# Run specific test class
dotnet test --filter "FullyQualifiedName~ShellViewModelTests"

# Run with coverage
dotnet test /p:CollectCoverage=true /p:CoverageFormat=opencover

# Watch mode (requires dotnet-watch)
dotnet watch test
```

**CI/CD Integration:**
- Configure in build pipeline (GitHub Actions, Azure Pipelines)
- Run tests on pull requests before merging
- Fail builds if coverage drops below target

---

*Testing analysis: 2026-02-17*
