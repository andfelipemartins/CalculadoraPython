# -*- coding: utf-8 -*-
"""
__main__.py

Ponto de entrada do pacote.

Permite:
- python -m calculadora
- comando "calculadora" (via [project.scripts] no pyproject.toml)

Importante:
- Evitamos nomear funções locais como "main" se também importamos "main" de outro módulo,
  para não criar recursão acidental.
"""

from __future__ import annotations

# Importa a função main da GUI com ALIAS para evitar colisão de nomes
from calculadora.app_tk import main as gui_main


def main() -> None:
    """Entry point do módulo/pacote."""
    gui_main()


if __name__ == "__main__":
    main()