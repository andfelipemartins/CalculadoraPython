# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

O formato segue uma linha simples inspirada em "Keep a Changelog" e versionamento por tags Git.

---

## [v0.1.0] - 2025-12-14

### Added
- Projeto empacotado em `src-layout` como pacote Python instalável (`pip install -e .`)
- Entry points:
  - `python -m calculadora`
  - comando `calculadora`
- GUI Tkinter integrada com a Engine
- Script `tasks.ps1` com atalhos (`init`, `test`, `run`)
- Normalização de EOL com `.gitattributes`

### Changed
- Imports organizados via pacote `calculadora`
- Testes atualizados para importar `calculadora.engine`

### Fixed
- Correção do entrypoint (`__main__.py`) para evitar recursão