# Changelog

All notable changes to LaTeXBuddy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- line numbers (!135)
- new test cases for multiple occurrences of own_checkers problems (!110)
- custom key for YaLafi problems (!109)
- filter for log files (!121)
- new base class for all modules and LatexBuddy (NamedModule`) (!108)
- new `Loggable` base class which provides a properly named logger to any class inheriting from it (!108)
- new module "NewerPublications" that checks for each entry in the BibTeX file if a newer publication exists (!120)
- new module "BibtexDuplicates" that checks the BibTeX file for similar entries (!120)
- debug message for beginning and end of whitelist check in `LatexBuddy` (!141)

### Changed
- the problem list and text is now scrollable (!135)
- language selection for aspell now works dynamically and using the config (!105)
- language codes are now standardized to fit different formats (!116)
- methods in ConfigLoader now take an instance or a type-descriptor of type NamedModule instead of taking the name as a string (!108)
- Problem API now takes an instance or a type-descriptor of type NamedModule instead of a string (!108)
- `NamedModule` is now the base class of `Module` and `MainModule` (therefore `LatexBuddy`) and provides a logger to all these classes by inheriting from `Loggable` (!108)
- all modules now use the new standards for ConfigLoader, Problem API and logging (!1ß8)
- `LatexBuddy` is now a singleton and inherits from `MainModule`, making it an instance of `NamedModule` as well (!108)
- modified format of `config.py`: options with key `"buddy"` are now located in a seperate dictionary (!108)
- languagetool now dynamically retrieves a list of supported languages from the commandline or (local/remote) server instead of comparing with a hardcoded list (!139)
- renamed tool_loader.py to module_loader.py and ToolLoader to ModuleLoader (!141)
- extracted an interface `ModuleProvider` from `ModuleLoader` and adjusted `LatexBuddy` and cli.py accordingly (!141)
- removed `LatexBuddy` methods `change_file` and `clear_error_list` and replaced their occurrences with `init` (!141)

### Fixed
- regex usage in own_checkers (!110)
- inconsistent naming of some checkers in config, Problem API and classnames (!108)
- shortened slightly lengthy methods in config_loader.py (!140)

## [0.3.0] - 15 Jun 2021

### Added
- centralized file for LaTeXBuddy exceptions (!94)
- checker to warn about low resolution in figures (!101)
- checker to detect \ref instead of e.g. \cref (!99)
- language support in whitelist for spelling or grammar errors (!102)
- added option to manually add keys and word lists to the whitelist via command line (!106)
- added Docker file for Docker-based install (!103)

### Changed
- moved module execution time measurements from individual modules to the main buddy instance (!93)
- improved logging for tool-methods find_executable and execute_no_errors (!94)
- adapted all modules using tool-methods find_executable and execute_no_errors to the new features (!94)
- changed module execution to utilize multiprocessing (!92)
- changed Problem attribute position to be optional (!96)
- renamed Problem attribute cid to p_type and made it optional (!102)
- whitelist file extension removed (!102)
- number of suggestions in a problem is now capped at 10 (!102)

### Fixed
- minor issue in languagetool.py: module didn't stop execution after java-check failed in find_languagetool_command() (!94)
- import issue with proselint, because proselint.py shared the same name with the imported API (!95)
- usage of old `compare_...` functions (#45, !97)
- whitelist working again (!102)
- invalid default value of cli flag `format` resulting in LaTeXBuddy ignoring the config option for `format` (#56, !104)

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


[Unreleased]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/v0.3.0...master
[0.3.0]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/v0.2.0...v0.3.0
[0.2.0]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/v0.1.0...v0.2.0
[0.1.0]: https://git.rz.tu-bs.de/sw-technik-fahrzeuginformatik/sep/sep-2021/ibr_alg_0/latexbuddy/-/compare/124d0730...v0.1.0
