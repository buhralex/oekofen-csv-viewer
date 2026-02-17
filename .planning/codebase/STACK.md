# Technology Stack

**Analysis Date:** 2026-02-17

## Languages

**Primary:**
- C# 12 - Desktop application development using .NET 8

## Runtime

**Environment:**
- .NET 8.0 (Windows-specific)
- Target: `net8.0-windows`

**Package Manager:**
- NuGet - .NET package management
- Project File: `OekoFEN_CSV_Viewer.csproj`

## Frameworks

**Core:**
- WPF (Windows Presentation Foundation) 8.0 - Desktop UI framework for Windows
- Stylet 1.3.7.0 - MVVM framework for WPF applications

**Data Visualization:**
- ScottPlot.WPF 5.0.47 - Scientific charting library for WPF

**Data Processing:**
- CsvHelper 33.0.1 - CSV file parsing and serialization library

## Key Dependencies

**Critical:**
- CsvHelper 33.0.1 - Handles CSV file import and parsing with attribute-based column mapping (used in `Models/OekoFenCSV.cs`)
- Stylet 1.3.7.0 - Provides IoC container (StyletIoC) and MVVM Screen base class (used in `Pages/ShellViewModel.cs`)
- ScottPlot.WPF 5.0.47 - Integrated in UI for data visualization (referenced in `Pages/ShellView.xaml`)

## Configuration

**Environment:**
- No external environment variables detected
- Single configuration entry point: `Bootstrapper.cs` (IoC container configuration)
- Application configuration via XAML declarative setup in `App.xaml`

**Build:**
- Project configuration via `OekoFEN_CSV_Viewer.csproj`
- Output Type: WinExe (Windows executable)
- Root Namespace: `OekoFEN_CSV_Viewer`

## Platform Requirements

**Development:**
- Visual Studio 2022 (.vs directory present)
- .NET 8 SDK
- Windows platform (WPF is Windows-only)

**Production:**
- Windows 10/11 runtime
- .NET 8.0 Windows runtime
- No external service dependencies

---

*Stack analysis: 2026-02-17*
