# -*- coding: utf-8 -*-
r"""
tests/test_engine.py

Suíte completa de testes da Engine (CalculatorEngine) usando pytest.

Objetivos:
- Garantir que a lógica funciona SEM GUI (princípio "cérebro primeiro")
- Cobrir casos do escopo (C, CE, Backspace, ±, ponto, + - * /, =)
- Validar comportamento com Decimal (precisão) e tratamento de erro (divisão por zero)
- Travar comportamentos de UX:
  - CE no meio da operação
  - Troca de operador sem digitar 2º operando
  - "=" repetido (repeat equals) e desarme ao iniciar nova entrada

Como rodar (na raiz do projeto):
    pytest
"""

from __future__ import annotations

from calculadora.engine import CalculatorEngine


# ----------------------------
# Helpers para manter os testes legíveis
# ----------------------------
def press(engine: CalculatorEngine, key: str) -> None:
    """Simula UMA tecla/ação na calculadora."""
    if key.isdigit() and len(key) == 1:
        engine.press_digit(key)
        return

    if key == ".":
        engine.press_decimal()
        return

    if key in {"+", "-", "*", "/", "×", "÷"}:
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

    if key in {"BS", "BACK", "BACKSPACE"}:
        engine.press_backspace()
        return

    if key in {"±", "SIGN"}:
        engine.press_toggle_sign()
        return

    raise ValueError(f"Tecla não suportada: {key!r}")


def press_seq(engine: CalculatorEngine, seq: list[str]) -> None:
    """Pressiona uma sequência de teclas."""
    for k in seq:
        press(engine, k)


def new_engine() -> CalculatorEngine:
    """Cria uma engine nova, garantindo estado inicial limpo."""
    return CalculatorEngine()


# ----------------------------
# Testes
# ----------------------------
def test_initial_state():
    eng = new_engine()
    assert eng.get_display() == "0"
    assert eng.get_secondary() == ""


def test_digit_entry_leading_zero_rules():
    eng = new_engine()

    press_seq(eng, ["0", "0", "0"])
    assert eng.get_display() == "0"

    press_seq(eng, ["1", "2", "3"])
    assert eng.get_display() == "123"


def test_decimal_entry_basic():
    eng = new_engine()

    press_seq(eng, ["0", ".", "5"])
    assert eng.get_display() == "0.5"

    press_seq(eng, ["C", "1", ".", "2"])
    assert eng.get_display() == "1.2"


def test_ignore_double_decimal():
    eng = new_engine()

    press_seq(eng, ["1", ".", "2", ".", "3"])
    assert eng.get_display() == "1.23"


def test_backspace_behavior():
    eng = new_engine()

    press_seq(eng, ["1", "2", "3", "BS"])
    assert eng.get_display() == "12"

    press_seq(eng, ["BS"])
    assert eng.get_display() == "1"

    press_seq(eng, ["BS"])
    assert eng.get_display() == "0"

    # backspace em 0 não muda
    press_seq(eng, ["BS"])
    assert eng.get_display() == "0"


def test_toggle_sign_behavior():
    eng = new_engine()

    press_seq(eng, ["9", "±"])
    assert eng.get_display() == "-9"

    press_seq(eng, ["±"])
    assert eng.get_display() == "9"

    # em zero, não deve virar "-0"
    press_seq(eng, ["C", "0", "±"])
    assert eng.get_display() == "0"


def test_clear_c_resets_everything():
    eng = new_engine()

    press_seq(eng, ["1", "2", "+"])
    assert eng.get_secondary() != ""

    press_seq(eng, ["C"])
    assert eng.get_display() == "0"
    assert eng.get_secondary() == ""


def test_clear_entry_ce_only_clears_current_entry():
    eng = new_engine()

    # 12 + 34, CE deve limpar o 34 (entrada atual), mantendo a operação pendente
    press_seq(eng, ["1", "2", "+", "3", "4", "CE"])
    assert eng.get_display() == "0"
    assert eng.get_secondary() != ""


def test_basic_addition():
    eng = new_engine()

    press_seq(eng, ["1", "0", "+", "2", "="])
    assert eng.get_display() == "12"


def test_basic_subtraction():
    eng = new_engine()

    press_seq(eng, ["9", "-", "5", "="])
    assert eng.get_display() == "4"


def test_basic_multiplication():
    eng = new_engine()

    press_seq(eng, ["6", "*", "7", "="])
    assert eng.get_display() == "42"


def test_basic_division():
    eng = new_engine()

    press_seq(eng, ["8", "/", "2", "="])
    assert eng.get_display() == "4"


def test_operator_chain_evaluates_left_to_right():
    eng = new_engine()

    # 10 + 2 + 3 = 15
    press_seq(eng, ["1", "0", "+", "2", "+", "3", "="])
    assert eng.get_display() == "15"


def test_equals_after_operator_uses_stored_value_as_rhs():
    eng = new_engine()

    # 5 + = => 10 (usa 5 como segundo operando)
    press_seq(eng, ["5", "+", "="])
    assert eng.get_display() == "10"


def test_secondary_display_shows_pending_expression():
    eng = new_engine()

    press_seq(eng, ["1", "0", "+"])
    assert eng.get_secondary().startswith("10")
    assert "+" in eng.get_secondary()


def test_division_by_zero_sets_error():
    eng = new_engine()

    press_seq(eng, ["9", "/", "0", "="])
    assert eng.get_display() in {"Erro", "Error"}


def test_error_recovery_by_typing_digit():
    eng = new_engine()

    press_seq(eng, ["9", "/", "0", "="])
    assert eng.get_display() in {"Erro", "Error"}

    press_seq(eng, ["7"])
    assert eng.get_display() == "7"


def test_error_recovery_by_clear():
    eng = new_engine()

    press_seq(eng, ["9", "/", "0", "="])
    press_seq(eng, ["C"])
    assert eng.get_display() == "0"
    assert eng.get_secondary() == ""


def test_decimal_precision_01_plus_02():
    eng = new_engine()

    press_seq(eng, ["0", ".", "1", "+", "0", ".", "2", "="])
    assert eng.get_display() == "0.3"


def test_input_overflow_is_ignored_not_error():
    eng = new_engine()

    press_seq(eng, ["C"])
    for _ in range(200):
        press(eng, "9")

    assert eng.get_display() != "Overflow"
    assert len(eng.get_display()) <= eng.MAX_DISPLAY_LEN


def test_ce_in_middle_of_operation_12_plus_7_ce_5_equals_17():
    eng = new_engine()
    press_seq(eng, ["1", "2", "+", "7", "CE", "5", "="])
    assert eng.get_display() == "17"


def test_operator_replacement_without_second_operand():
    eng = new_engine()
    press_seq(eng, ["1", "0", "+", "-", "2", "="])
    assert eng.get_display() == "8"


def test_repeat_equals_repeats_last_operation():
    eng = new_engine()
    press_seq(eng, ["5", "+", "2", "=", "=", "="])
    assert eng.get_display() == "11"


def test_repeat_equals_is_disarmed_when_user_starts_new_entry():
    eng = new_engine()
    press_seq(eng, ["5", "+", "2", "=", "1", "="])
    assert eng.get_display() == "1"