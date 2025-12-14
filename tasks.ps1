<#
tasks.ps1 — atalhos do projeto (Windows/PowerShell)

Uso:
  .\tasks.ps1 init     # cria venv + instala em modo editable
  .\tasks.ps1 test     # roda pytest
  .\tasks.ps1 run      # roda GUI (python -m calculadora)
  .\tasks.ps1 fmt      # (reservado) formatação futura
#>

param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("init","test","run","fmt")]
  [string]$Task
)

$ErrorActionPreference = "Stop"

function Ensure-Venv {
  if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Criando venv em .venv..."
    python -m venv .venv
  }
  Write-Host "Ativando venv..."
  & .\.venv\Scripts\Activate.ps1
}

switch ($Task) {
  "init" {
    Ensure-Venv
    python -m pip install -U pip
    python -m pip install -e .
    Write-Host "OK: ambiente pronto."
  }
  "test" {
    Ensure-Venv
    pytest
  }
  "run" {
    Ensure-Venv
    python -m calculadora
  }
  "fmt" {
    Ensure-Venv
    Write-Host "Ainda não configurado. (Etapa futura: black/ruff/isort)"
  }
}