from decimal import Decimal, getcontext


class CalculatorEngine:
    """
    Engine (cérebro) da calculadora.
    - UI não faz conta: só chama esses métodos e desenha display_text/secondary.
    - Usa Decimal pra precisão.
    Observação: getcontext().prec é global; ok para app desktop simples.
    """

    MAX_DISPLAY_LEN = 32  # limite "visual" (proteção de UX + segurança)

    def __init__(self):
        # Precisão padrão do Decimal (ajuste se quiser depois)
        getcontext().prec = 28
        self.reset()

    # -------------------------
    # Estado / Display
    # -------------------------
    def reset(self):
        self.display_text = "0"
        self.display_secondary = ""

        self.stored_value = None  # Decimal | None
        self.pending_op = None  # str | None

        self.reset_next_digit = False
        self.error_state = False

    def get_display(self) -> str:
        return self.display_text

    def get_secondary(self) -> str:
        return self.display_secondary

    # -------------------------
    # Helpers
    # -------------------------
    def _set_error(self, msg="Erro"):
        self.display_text = msg
        self.display_secondary = ""
        self.stored_value = None
        self.pending_op = None
        self.reset_next_digit = True
        self.error_state = True

    def _clear_error_full(self):
        # erro é estado inconsistente -> reset total é o mais seguro
        self.reset()

    def _to_decimal(self, text: str) -> Decimal:
        """
        Converte display_text para Decimal de forma segura.
        Aceita '12.' (tratado como 12). Nunca será chamado se display for 'Erro'.
        """
        t = text.strip()

        if t in ("", "-", ".", "-."):
            return Decimal("0")

        # se terminar com '.', remove para converter
        if t.endswith("."):
            t = t[:-1]
            if t in ("", "-"):
                return Decimal("0")

        return Decimal(t)

    def _format_decimal(self, value: Decimal) -> str:
        # evita "-0"
        if value == 0:
            return "0"

        s = format(value, "f")  # fixa (sem notação científica)
        # remove zeros à direita
        if "." in s:
            s = s.rstrip("0").rstrip(".")

        # Se estourar o display por resultado de cálculo, aqui ainda é aceitável
        # marcar Overflow (é diferente de "digitou demais").
        if len(s) > self.MAX_DISPLAY_LEN:
            self._set_error("Overflow")
            return self.display_text

        return s

    def _apply_op(self, a: Decimal, op: str, b: Decimal) -> Decimal:
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op in ("*", "×"):
            return a * b
        if op in ("/", "÷"):
            if b == 0:
                raise ZeroDivisionError
            return a / b
        raise ValueError(f"Operador inválido: {op}")

    def _start_new_entry_if_needed(self):
        if self.reset_next_digit:
            self.display_text = "0"
            self.reset_next_digit = False

    # -------------------------
    # Teclas (inputs)
    # -------------------------
    def press_digit(self, d: str):
        if not (isinstance(d, str) and len(d) == 1 and d.isdigit()):
            return

        if self.error_state:
            self._clear_error_full()

        self._start_new_entry_if_needed()

        # UX: se já atingiu o limite, IGNORA o novo dígito (sem "Overflow" punitivo)
        if self.display_text != "0" and len(self.display_text) >= self.MAX_DISPLAY_LEN:
            return

        if self.display_text == "0":
            self.display_text = d
        else:
            self.display_text += d

    def press_decimal(self):
        if self.error_state:
            self._clear_error_full()

        self._start_new_entry_if_needed()

        # UX: se já tá no limite, ignora também
        if len(self.display_text) >= self.MAX_DISPLAY_LEN:
            return

        if "." not in self.display_text:
            self.display_text += "."

    def press_backspace(self):
        if self.error_state:
            self._clear_error_full()
            return

        self._start_new_entry_if_needed()

        if self.display_text == "0":
            return

        self.display_text = self.display_text[:-1]

        # se sobrar só "-" ou vazio, volta pra 0
        if self.display_text in ("", "-"):
            self.display_text = "0"

        if self.display_text == "-0":
            self.display_text = "0"

    def press_toggle_sign(self):
        if self.error_state:
            self._clear_error_full()

        self._start_new_entry_if_needed()

        # se for zero (inclusive "0."), não troca sinal
        current = self._to_decimal(self.display_text)
        if current == 0:
            return

        if self.display_text.startswith("-"):
            self.display_text = self.display_text[1:]
        else:
            # UX: garantir que adicionar "-" não estoure limite
            if len(self.display_text) + 1 > self.MAX_DISPLAY_LEN:
                return
            self.display_text = "-" + self.display_text

    def press_clear(self):
        self.reset()

    def press_clear_entry(self):
        if self.error_state:
            self._clear_error_full()
            return

        self.display_text = "0"
        self.reset_next_digit = False

    def press_operator(self, op: str):
        if self.error_state:
            return

        op = op.strip()
        if op not in {"+", "-", "*", "×", "/", "÷"}:
            return
        if op == "×":
            op = "*"
        if op == "÷":
            op = "/"

        current = self._to_decimal(self.display_text)

        # encadeamento: se já havia operação pendente e o usuário digitou o 2º operando,
        # calcula antes de trocar o operador
        if self.pending_op is not None and self.stored_value is not None and not self.reset_next_digit:
            try:
                result = self._apply_op(self.stored_value, self.pending_op, current)
            except ZeroDivisionError:
                self._set_error("Erro")
                return

            self.stored_value = result
            self.display_text = self._format_decimal(result)
            if self.error_state:
                return

        if self.stored_value is None:
            self.stored_value = current

        self.pending_op = op
        # display secundário: "10 +"
        self.display_secondary = f"{self._format_decimal(self.stored_value)} {op}"
        if self.error_state:
            return

        self.reset_next_digit = True

    def press_equals(self):
        if self.error_state:
            return

        if self.pending_op is None or self.stored_value is None:
            return

        current = self._to_decimal(self.display_text)

        # "=" logo após operador: usa stored_value como segundo operando (5 + = -> 10)
        if self.reset_next_digit:
            current = self.stored_value

        try:
            result = self._apply_op(self.stored_value, self.pending_op, current)
        except ZeroDivisionError:
            self._set_error("Erro")
            return

        self.display_text = self._format_decimal(result)
        self.display_secondary = ""

        self.stored_value = None
        self.pending_op = None
        self.reset_next_digit = True


if __name__ == "__main__":
    eng = CalculatorEngine()

    # sanity checks rápidos
    eng.press_digit("0")
    eng.press_decimal()
    eng.press_digit("1")
    eng.press_operator("+")
    eng.press_digit("0")
    eng.press_decimal()
    eng.press_digit("2")
    eng.press_equals()
    print("0.1 + 0.2 =", eng.get_display())  # esperado: 0.3

    eng.press_operator("/")
    eng.press_digit("0")
    eng.press_equals()
    print("Div por zero =", eng.get_display())  # esperado: Erro

    eng.press_digit("9")  # deve sair do erro e iniciar novo número
    eng.press_toggle_sign()
    print("± em 9 =", eng.get_display())  # esperado: -9

    # overflow na digitação (não deve virar erro, só ignorar dígitos extras)
    eng.press_clear()
    for _ in range(100):
        eng.press_digit("9")
    print("Len display (<=32):", len(eng.get_display()), eng.get_display())