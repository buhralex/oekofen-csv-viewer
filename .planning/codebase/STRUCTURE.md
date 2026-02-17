# Codebase Structure

**Analysis Date:** 2026-02-17

## Directory Layout

```
OekoFEN_CSV_Viewer/
├── .planning/           # GSD planning documents
├── .vs/                 # Visual Studio IDE cache (not committed)
├── bin/                 # Build output (not committed)
├── obj/                 # Intermediate build files (not committed)
├── Files/               # Sample data and assets
│   ├── graph_20260216.png
│   └── touch_20260216.csv
├── Models/              # Data models and domain objects
│   └── OekoFenCSV.cs
├── Pages/               # MVVM Views and ViewModels
│   ├── ShellView.xaml
│   ├── ShellView.xaml.cs
│   └── ShellViewModel.cs
├── App.xaml             # WPF application root
├── App.xaml.cs          # Application code-behind
├── Bootstrapper.cs      # IoC container and app initialization
└── OekoFEN_CSV_Viewer.csproj  # Project configuration
```

## Directory Purposes

**Models/:**
- Purpose: Domain model classes representing CSV data structures
- Contains: Data Transfer Objects (DTOs) with CsvHelper mapping attributes
- Key files: `OekoFenCSV.cs`

**Pages/:**
- Purpose: MVVM presentation layer - Views (XAML UI) and ViewModels (logic)
- Contains: Window definitions with xaml markup, code-behind interaction logic, and view model state/commands
- Key files: `ShellView.xaml`, `ShellView.xaml.cs`, `ShellViewModel.cs`

**Files/:**
- Purpose: Sample data and testing assets
- Contains: CSV data files and graph images for reference
- Key files: `touch_20260216.csv` (test CSV), `graph_20260216.png` (reference image)

## Key File Locations

**Entry Points:**
- `App.xaml`: WPF application root, bootstrapper registration
- `Bootstrapper.cs`: IoC container setup and application initialization
- `Pages/ShellView.xaml`: Main application window UI

**Configuration:**
- `OekoFEN_CSV_Viewer.csproj`: Project settings, target framework (net8.0-windows), NuGet dependencies

**Core Logic:**
- `Pages/ShellViewModel.cs`: CSV import logic, file dialog handling, records processing
- `Models/OekoFenCSV.cs`: CSV record schema definition

**Data:**
- `Files/touch_20260216.csv`: Sample CSV file for testing

## Naming Conventions

**Files:**
- ViewModels: `{FeatureName}ViewModel.cs` (e.g., `ShellViewModel.cs`)
- Views: `{FeatureName}View.xaml` (e.g., `ShellView.xaml`)
- Models: PascalCase descriptive name (e.g., `OekoFenCSV.cs`)
- Code-behind: `{FeatureName}View.xaml.cs` (matches View name)

**Directories:**
- Feature areas: PascalCase plural (e.g., `Pages/`, `Models/`)
- Avoid single-responsibility directories with identical names to classes

**Classes:**
- ViewModels: `[Name]ViewModel` inheriting from `Screen` (Stylet convention)
- Models: PascalCase (e.g., `OekoFenCSV`)
- Code-behind: Same as XAML file name

**Methods:**
- Commands: PascalCase verbs (e.g., `ImportCSVFile()`)
- Properties: PascalCase (e.g., `MyProperty`)

## Where to Add New Code

**New Feature (e.g., Export CSV):**
- ViewModel: `Pages/{FeatureName}ViewModel.cs` (inherit from `Screen`)
- View: `Pages/{FeatureName}View.xaml` + `Pages/{FeatureName}View.xaml.cs`
- Models if needed: `Models/{ModelName}.cs`

**New Model/DTO:**
- Location: `Models/{ModelName}.cs`
- Pattern: Public properties with CsvHelper attributes if CSV-related
- No dependencies on Views or ViewModels

**New Page/Feature:**
- Create folder: `Pages/{FeatureName}/` (optional, if feature is substantial)
- Files: `{FeatureName}View.xaml`, `{FeatureName}View.xaml.cs`, `{FeatureName}ViewModel.cs`
- Register in `Bootstrapper.cs` if requires custom IoC binding

**Utilities/Helpers:**
- Location: Create `Services/` or `Helpers/` directory at root level if utility is cross-cutting
- Pattern: Static classes or injectable service interfaces

## Special Directories

**bin/ and obj/:**
- Purpose: Build output and intermediate compilation artifacts
- Generated: Yes (automatically by C# build process)
- Committed: No (in .gitignore)

**Files/:**
- Purpose: Sample data for testing and reference
- Generated: No (manually added)
- Committed: Yes (part of repo for testing)

**.vs/:**
- Purpose: Visual Studio IDE metadata and cache
- Generated: Yes (automatically by Visual Studio)
- Committed: No (in .gitignore)

## Project Configuration

**Target Framework:** .NET 8.0 Windows (`net8.0-windows`)

**Key Dependencies:**
- `Stylet` v1.3.7.0 - MVVM framework with IoC container
- `CsvHelper` v33.0.1 - CSV parsing and serialization
- `ScottPlot.WPF` v5.0.47 - WPF charting library

**Application Type:** WinExe (Windows desktop executable)

**WPF Enabled:** Yes (UseWPF = true)
