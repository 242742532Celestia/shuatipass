# Changelog

All notable changes to shuatipass will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-17

### Added
- **D1**: PDF parser core (PyMuPDF) with 4 built-in question types
- **D2**: bbox cutting, essay detection, embedded option splitting
- **D3**: CLI + Python library (parse / stats / info / configs)
- **D4**: YAML config system with 4 built-in presets (xuekewang / generic / zujuan / textbook)
- **D5**: Documentation (tutorial / api / config / examples / docker / publish / web)
- **D6**: Docker multi-stage build + docker-compose
- **D7**: GitHub Actions CI (Python 3.10/3.11/3.12 + lint + build)
- **D8**: PyPI publish prep + wheel built
- **D9**: Auto-detect PDF source + 2 new configs
- **D10**: Formula OCR (Mathpix API + pix2tex)
- **D11**: AI question generator (3 providers: MiniMax / OpenAI / Anthropic)
- **D12**: Exam Mimic 完整版 + 错题本 (mark / export / HTML)

### Features
- 9 CLI subcommands: `parse`, `stats`, `info`, `configs`, `ocr`, `web`, `generate`, `exam-mimic`, `wrongbook`
- 100 unit tests + 6 skipped (with gradio)
- 7 documentation files in `docs/`
- 7 example scripts in `examples/`
- Gradio Web UI with one-click parse
- MIT License
- PyPI-ready packaging

[Unreleased]: https://github.com/<owner>/shuatipass/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<owner>/shuatipass/releases/tag/v0.1.0
