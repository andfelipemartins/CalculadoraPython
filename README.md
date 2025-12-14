![Tests](https://github.com/andfelipemartins/CalculadoraPython/actions/workflows/tests.yml/badge.svg)

# Calculadora (Python) — Engine testável + GUI Tkinter

Projeto de calculadora com arquitetura **“cérebro primeiro”**:
- **Engine** (lógica) independente de GUI e coberta por testes (`pytest`)
- **GUI Tkinter** apenas como camada de interface
- Estrutura de pacote real (`src-layout`) instalável em modo desenvolvimento (`pip install -e .`)

---

## Requisitos

- Python 3.10+ (recomendado 3.11+)
- Windows (GUI Tkinter) — em outros SOs também funciona, desde que Tkinter esteja disponível

---

## Setup do ambiente (Windows / PowerShell)

Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .

## Atalhos (Windows / PowerShell)

```powershell
.\tasks.ps1 init
.\tasks.ps1 test
.\tasks.ps1 run


### 3) Commit + push

```powershell
git add tasks.ps1 README.md
git commit -m "docs: add tasks script for common commands"
git push