# Changelog

All notable changes to LaTeXBuddy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- centralized file for LaTeXBuddy exceptions (!94)

### Changed
- moved module execution time measurements from individual modules to the main buddy instance (!93)
- improved logging for tool-methods find_executable and execute_no_errors (!94)
- adapted all modules using tool-methods find_executable and execute_no_errors to the new features (!94)
- changed module execution to utilize multiprocessing (!92)
- changed Problem attribute position to be optional (!96)

### Fixed
- minor issue in languagetool.py: module didn't stop execution after java-check failed in find_languagetool_command() (!94)

## [0.2.0] - 08 Jun 2021

### Added

- button, to add to whitelist (!87)
- configuration files (!30)
- abstraction around the checked file using `TexFile` class (!45, !46)
- tool loader (!47)
- ability to select modules to be run (!48)
- CI job for publishing the package to the Registry (!51)
- error highlighting inside HTML output (!52)
- legal and copyright notices (!54)
- Proselint module (!60)
- various on-house modules
  - unreferenced figures (!65)
  - SiUnitX (!66, !67)
  - empty section (!68)
  - use of `\url` (!69)
- better logging (!73)
  - clearer, colourful console output
  - file log containing more verbose information
- verification options for config entries (!76)
- `--version`/`-v` option to the CLI (!83)
- in-file preprocessor for .tex files (!84)

### Changed

- **BREAKING CHANGE:** minimal Python version set to 3.6.8 (!81)
- modules now adhere to the Abstract Module API (!22, !46)
- errors renamed to problems and now use new API (!42, !46)
- all modules that use the config now validate the config entries (!76)
- removed test_module.py (!77)
- improved spacing and sizing of the logo (!82)
- modules now adhere to the Abstract Module API (!22, !46)
- errors renamed to problems and now use new API (!42, !46)
- removed test_module.py (!77)

### Fixed

- Aspell positions of problems in source file (!53, !55)
- HTML output not working properly with new APIs (!56)
- ChkTeX working incorrectly with text containing `:` (!70)
- Minor inconsistency in typing for Problem constructor's parameters (!75)
- unwanted spaces around problem text in HTML output (!80)

## [0.1.0] - 18 May 2021

This is the first (pre-)release of LaTeXBuddy.

### Added

- basic project files (!1)
- main module functionality (!3)
- results output
  - HTML (!2, !25, !29)
  - JSON (!3)
- basic interoperability with non-Python checkers (!5, !6, !10)
- modules
  - LanguageTool (!3)
  - ChkTeX (!4)
  - Aspell (!5, !7, !8)
- whitelist (!21)
- tools
- command-line interface (!17)
- various development improvements
  - CI jobs for linting (!18) and smoke tests (!33)
- draft of the abstract module API (!22)
- logo (!38)


[Unreleased]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/v0.2.0...master
[0.2.0]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/v0.1.0...v0.2.0
[0.1.0]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/124d0730...v0.1.0
