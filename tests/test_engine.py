# -*- coding: utf-8 -*-
"""
tests/test_engine.py

Testes da Engine (CalculatorEngine) usando pytest.

Objetivos:
- Garantir que a lógica funciona SEM GUI (princípio "cérebro primeiro")
- Cobrir os casos obrigatórios do escopo (C, CE, Backspace, ±, ponto, + - * /, =)
- Validar comportamento com Decimal (precisão) e tratamento de erro (divisão por zero)

Como rodar (na raiz do projeto C:\\Calculadora):
    pytest -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# --- Import da engine sem exigir que "src" seja um pacote ---
# Isso evita ter que criar src/__init__.py agora.
ROOT = Path(__file__).resolve().parents[1]  # ...\Calculadora
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from engine import CalculatorEngine  # noqa: E402


# ---------------------------
# Helpers
# ---------------------------

def press(engine: CalculatorEngine, key: str) -> None:
    """
    Simula uma tecla/ação única na calculadora.
    Mantém os testes legíveis e próximos do "uso real".
    """
    if key.isdigit() and len(key) == 1:
        engine.press_digit(key)
        return

    if key == ".":
        engine.press_decimal()
        return

    if key in {"+", "-", "*", "×", "/", "÷"}:
        engine.press_operator(key)
        return

    if key == "=":
        engine.press_equals()
        return

    if key == "C":
        engine.press_clear()
        return

    if key == "CE":
        engine.press_clear_entry()
        return

    if key in {"BS", "BACKSPACE"}:
        engine.press_backspace()
        return

    if key in {"±", "SIGN"}:
        engine.press_toggle_sign()
        return

    raise ValueError(f"Tecla não suportada no helper de teste: {key!r}")


def feed(engine: CalculatorEngine, keys: list[str]) -> str:
    """Aplica uma sequência de teclas e retorna o display final."""
    for k in keys:
        press(engine, k)
    return engine.get_display()


@pytest.fixture()
def eng() -> CalculatorEngine:
    """Fixture padrão: engine nova em cada teste."""
    return CalculatorEngine()


# ---------------------------
# Testes básicos de estado
# ---------------------------

def test_initial_state(eng: CalculatorEngine):
    assert eng.get_display() == "0"
    assert eng.get_secondary() == ""


def test_digit_entry_leading_zero_rules(eng: CalculatorEngine):
    # "0" seguido de "0" continua "0"
    assert feed(eng, ["0", "0"]) == "0"

    # "0" seguido de "5" vira "5" (não "05")
    eng.press_clear()
    assert feed(eng, ["0", "5"]) == "5"

    # concatenação normal
    eng.press_clear()
    assert feed(eng, ["1", "2", "3"]) == "123"


# ---------------------------
# Decimal / ponto / backspace / sinal
# ---------------------------

def test_decimal_entry_basic(eng: CalculatorEngine):
    # Apertar "." no início vira "0."
    assert feed(eng, ["."]) == "0."

    # Depois "5" vira "0.5"
    assert feed(eng, ["5"]) == "0.5"


def test_ignore_double_decimal(eng: CalculatorEngine):
    # Caso obrigatório do escopo: 1 . 2 . 3 -> "1.23"
    assert feed(eng, ["1", ".", "2", ".", "3"]) == "1.23"


def test_backspace_behavior(eng: CalculatorEngine):
    assert feed(eng, ["4", "5"]) == "45"
    press(eng, "BS")
    assert eng.get_display() == "4"
    press(eng, "BS")
    assert eng.get_display() == "0"
    press(eng, "BS")  # não deve ficar vazio
    assert eng.get_display() == "0"


def test_toggle_sign_behavior(eng: CalculatorEngine):
    # 9 ± -> -9 (obrigatório)
    assert feed(eng, ["9", "±"]) == "-9"

    # -9 ± -> 9
    assert feed(eng, ["±"]) == "9"

    # 0 ± -> continua 0 (regra de UX comum)
    eng.press_clear()
    assert feed(eng, ["0", "±"]) == "0"


# ---------------------------
# Operações e comandos C/CE
# ---------------------------

def test_clear_c_resets_everything(eng: CalculatorEngine):
    feed(eng, ["1", "2", "+", "3"])
    press(eng, "C")
    assert eng.get_display() == "0"
    assert eng.get_secondary() == ""


def test_clear_entry_ce_only_clears_current_entry(eng: CalculatorEngine):
    # Caso obrigatório do escopo:
    # 12 + 7 (CE) 5 =  -> 17
    assert feed(eng, ["1", "2", "+", "7", "CE", "5", "="]) == "17"


def test_basic_addition(eng: CalculatorEngine):
    assert feed(eng, ["1", "0", "+", "2", "="]) == "12"


def test_basic_subtraction(eng: CalculatorEngine):
    assert feed(eng, ["1", "0", "-", "3", "="]) == "7"


def test_basic_multiplication(eng: CalculatorEngine):
    assert feed(eng, ["6", "*", "7", "="]) == "42"


def test_basic_division(eng: CalculatorEngine):
    assert feed(eng, ["8", "/", "2", "="]) == "4"


def test_chained_operations_left_to_right(eng: CalculatorEngine):
    # Encadeamento que a engine implementa:
    # 10 + 2 - 3 = 9
    assert feed(eng, ["1", "0", "+", "2", "-", "3", "="]) == "9"


def test_equals_after_operator_uses_stored_value(eng: CalculatorEngine):
    # Comportamento definido no código:
    # 5 + =  -> 10 (repete o stored_value como segundo operando)
    assert feed(eng, ["5", "+", "="]) == "10"


# ---------------------------
# Erros e recuperação
# ---------------------------

def test_division_by_zero_sets_error(eng: CalculatorEngine):
    # Caso obrigatório: 5 ÷ 0 = -> "Erro"
    assert feed(eng, ["5", "/", "0", "="]) == "Erro"


def test_error_recovery_by_typing_digit(eng: CalculatorEngine):
    # Após erro, digitar um dígito deve iniciar nova entrada (UX mais suave que "travado até C")
    feed(eng, ["5", "/", "0", "="])
    assert eng.get_display() == "Erro"

    press(eng, "9")
    assert eng.get_display() == "9"


def test_error_recovery_by_clear(eng: CalculatorEngine):
    feed(eng, ["5", "/", "0", "="])
    press(eng, "C")
    assert eng.get_display() == "0"


# ---------------------------
# Precisão Decimal (obrigatório)
# ---------------------------

def test_decimal_precision_01_plus_02(eng: CalculatorEngine):
    # Caso obrigatório: 0.1 + 0.2 = -> "0.3" (sem lixo de float)
    assert feed(eng, ["0", ".", "1", "+", "0", ".", "2", "="]) == "0.3"


# ---------------------------
# Overflow de digitação (UX: ignorar dígito extra)
# ---------------------------

def test_input_overflow_is_ignored_not_error(eng: CalculatorEngine):
    # A engine deve IGNORAR dígitos além do MAX_DISPLAY_LEN (sem mandar "Overflow" por digitação)
    for _ in range(200):
        press(eng, "9")

    s = eng.get_display()
    assert s != "Overflow"
    assert len(s) <= eng.MAX_DISPLAY_LEN
    # deve ser uma sequência de '9'
    assert set(s) == {"9"} or s == "0"