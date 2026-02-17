# Architecture

**Analysis Date:** 2026-02-17

## Pattern Overview

**Overall:** MVVM (Model-View-ViewModel) with Stylet IoC Container

**Key Characteristics:**
- WPF desktop application using the MVVM pattern
- Separation of concerns: Models, Views, ViewModels
- Dependency injection via Stylet IoC container for loose coupling
- Data binding between XAML Views and ViewModels
- No explicit Service Layer in current implementation

## Layers

**Presentation Layer (View):**
- Purpose: Display UI and handle user interactions
- Location: `Pages/` directory
- Contains: XAML markup files (.xaml) and code-behind (.xaml.cs)
- Depends on: ViewModels for data binding and commands
- Used by: WPF runtime and end users

**Presentation Logic Layer (ViewModel):**
- Purpose: Bind data to UI, expose commands, manage UI state
- Location: `Pages/ShellViewModel.cs`
- Contains: Screen class (Stylet base), properties, methods
- Depends on: Models, external libraries (CsvHelper, Microsoft.Win32)
- Used by: Views through data binding and command routing

**Data Layer (Model):**
- Purpose: Represent domain data structures (CSV records)
- Location: `Models/OekoFenCSV.cs`
- Contains: Data classes with CsvHelper attributes
- Depends on: CsvHelper for attribute mapping
- Used by: ViewModels for deserialization and data handling

**Application Bootstrap Layer:**
- Purpose: Initialize and configure the application
- Location: `Bootstrapper.cs`, `App.xaml`, `App.xaml.cs`
- Contains: IoC container setup, application lifecycle hooks
- Depends on: Stylet framework
- Used by: WPF runtime on startup

## Data Flow

**CSV Import Flow:**

1. User clicks "Open" menu item in `ShellView.xaml`
2. Command routing invokes `ShellViewModel.ImportCSVFile()`
3. OpenFileDialog displayed to user for file selection
4. CsvReader reads selected file with configured CsvConfiguration
5. CSV lines deserialized into `OekoFenCSV` model objects
6. Records iterated and output to Debug console
7. (Placeholder) Future: Display data in WpfPlot chart

**State Management:**
- ViewModel maintains minimal state: `MyProperty` (unused)
- No persistent state between operations
- Dialog state managed by Windows OpenFileDialog
- UI state driven by ViewModel property changes through data binding

## Key Abstractions

**ShellViewModel (Screen):**
- Purpose: Main application window logic and CSV import orchestration
- Examples: `Pages/ShellViewModel.cs`
- Pattern: Inherits from Stylet `Screen` base class which provides INotifyPropertyChanged

**OekoFenCSV (Model):**
- Purpose: CSV record representation with indexed columns
- Examples: `Models/OekoFenCSV.cs`
- Pattern: POCO (Plain Old CLR Object) with CsvHelper Index attributes for column mapping

## Entry Points

**Application Entry:**
- Location: `App.xaml` and `Bootstrapper.cs`
- Triggers: Windows launches executable
- Responsibilities: Configure IoC container, instantiate ShellViewModel, display ShellView

**Primary Feature Entry:**
- Location: `Pages/ShellViewModel.ImportCSVFile()`
- Triggers: File → Open menu command (routed from View)
- Responsibilities: File dialog, CSV parsing, record processing

## Error Handling

**Strategy:** Minimal - no explicit error handling in current implementation

**Patterns:**
- OpenFileDialog returns null/false if cancelled (checked with `== true`)
- CsvReader exceptions not caught (will propagate to WPF runtime)
- No validation of CSV format or data integrity

## Cross-Cutting Concerns

**Logging:** `System.Diagnostics.Debug.WriteLine()` for console output during CSV import

**Validation:** CsvHelper performs implicit validation via Index attributes and type casting

**Authentication:** Not applicable - desktop application with no auth

**UI Binding:** Stylet provides automatic View-ViewModel binding via type naming convention (ShellView ↔ ShellViewModel)
