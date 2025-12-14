from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext


class CalculatorEngine:
    """
    Engine (cérebro) da calculadora.
    - A GUI NÃO faz contas. Ela só chama esses métodos e desenha display_text/secondary.
    - Usa Decimal para precisão.
    """

    # Limite visual do display (proteção de UX + evita números absurdos no display)
    MAX_DISPLAY_LEN = 32

    def __init__(self):
        # Precisão padrão do Decimal (global do contexto)
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

        # ✅ Etapa: suporte a "=" repetido (repeat equals)
        # Guarda a última operação confirmada por "=".
        self.last_op = None  # str | None
        self.last_rhs = None  # Decimal | None (último operando à direita)

    def get_display(self) -> str:
        return self.display_text

    def get_secondary(self) -> str:
        return self.display_secondary

    # -------------------------
    # Helpers
    # -------------------------
    def _set_error(self, msg="Erro"):
        """
        Entra em estado de erro (display principal mostra msg).
        - zera operação pendente/armazenada
        - limpa display secundário
        """
        self.display_text = msg
        self.display_secondary = ""
        self.stored_value = None
        self.pending_op = None
        self.reset_next_digit = True
        self.error_state = True

        # Em erro, não faz sentido manter repeat-equals.
        self.last_op = None
        self.last_rhs = None

    def _clear_error_full(self):
        """Sai do erro e reseta completamente."""
        self.reset()

    def _to_decimal(self, text: str) -> Decimal:
        """
        Converte o texto do display para Decimal.
        - Aceita "0", "-0", "12", "-12", "0.", "-0.", "12.", "12.34"
        - Converte vírgula para ponto por segurança.
        """
        t = str(text).strip().replace(",", ".")

        if t in ("", "-", ".", "-."):
            return Decimal("0")

        # Se terminar com '.', remove para converter
        if t.endswith("."):
            t = t[:-1]
            if t in ("", "-"):
                return Decimal("0")

        return Decimal(t)

    @staticmethod
    def _op_for_display(op: str) -> str:
        """Converte operador interno para símbolo bonito (apenas UX)."""
        return {
            "+": "+",
            "-": "−",
            "*": "×",
            "/": "÷",
        }.get(op, op)

    def _format_decimal(self, value: Decimal) -> str:
        """Formata Decimal para o display principal.

        Regras:
        - Evita notação científica (sempre em forma fixa quando possível)
        - Remove zeros desnecessários à direita
        - Se exceder MAX_DISPLAY_LEN por causa da parte decimal, tenta arredondar para caber
        - Se nem a parte inteira couber, marca Overflow
        """

        # Evita aparecer "-0" no display.
        if value == 0:
            return "0"

        # Primeiro tenta forma fixa normal (sem notação científica)
        s = format(value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")

        # Se já couber, ótimo
        if len(s) <= self.MAX_DISPLAY_LEN:
            return s

        # Se existe parte decimal e estourou, tentamos arredondar as casas decimais para caber
        if "." in s:
            for _ in range(6):
                sign = "-" if value < 0 else ""
                abs_fixed = format(abs(value), "f")
                int_part = abs_fixed.split(".", 1)[0]

                # Se nem o inteiro cabe, não há o que fazer
                if len(sign) + len(int_part) > self.MAX_DISPLAY_LEN:
                    self._set_error("Overflow")
                    return self.display_text

                # Espaço máximo para a fração (considerando o ponto)
                allowed_frac = self.MAX_DISPLAY_LEN - len(sign) - len(int_part) - 1
                if allowed_frac <= 0:
                    # Sem espaço para fração -> mostra apenas o inteiro
                    return sign + int_part

                # Ex.: allowed_frac=3 -> quant = 0.001
                quant = Decimal("1").scaleb(-allowed_frac)

                try:
                    value = value.quantize(quant, rounding=ROUND_HALF_UP)
                except (InvalidOperation, ValueError):
                    self._set_error("Overflow")
                    return self.display_text

                s = format(value, "f")
                if "." in s:
                    s = s.rstrip("0").rstrip(".")

                if len(s) <= self.MAX_DISPLAY_LEN:
                    return s

            self._set_error("Overflow")
            return self.display_text

        # Caso extremo: sem ponto e não coube -> overflow real (inteiro grande demais)
        self._set_error("Overflow")
        return self.display_text

    def _apply_op(self, a: Decimal, op: str, b: Decimal) -> Decimal:
        """
        Aplica operação com Decimal.
        Pode levantar ZeroDivisionError (tratado pelo chamador).
        """
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

    def _clear_repeat_memory_if_free(self):
        """
        ✅ Etapa: se a operação anterior já terminou (sem pending_op/stored_value),
        e o usuário começar a editar/entrar novos números, limpamos o repeat-equals
        para evitar comportamento surpreendente (ex.: digitar um novo número e apertar '='
        aplicar a operação anterior sem o usuário pedir).
        """
        if self.pending_op is None and self.stored_value is None:
            self.last_op = None
            self.last_rhs = None

    def _start_new_entry_if_needed(self):
        """
        Quando reset_next_digit está True, significa que a próxima entrada numérica
        deve começar do zero (ex.: depois de apertar operador ou '=')
        """
        if self.reset_next_digit:
            self.display_text = "0"
            self.reset_next_digit = False

            # Começando uma nova entrada, desarma repeat-equals (UX previsível).
            self._clear_repeat_memory_if_free()

    # -------------------------
    # Teclas (inputs)
    # -------------------------
    def press_digit(self, d: str):
        """Digite 0-9."""
        if not (isinstance(d, str) and len(d) == 1 and d.isdigit()):
            return

        if self.error_state:
            self._clear_error_full()

        self._start_new_entry_if_needed()

        # UX: se já atingiu o limite, ignora o novo dígito (não entra em erro)
        if self.display_text != "0" and len(self.display_text) >= self.MAX_DISPLAY_LEN:
            return

        if self.display_text == "0":
            self.display_text = d
        elif self.display_text == "-0":
            self.display_text = "-" + d
        else:
            self.display_text += d

    def press_decimal(self):
        """Insere ponto decimal."""
        if self.error_state:
            self._clear_error_full()

        self._start_new_entry_if_needed()

        if "." in self.display_text:
            return

        if len(self.display_text) >= self.MAX_DISPLAY_LEN:
            return

        self.display_text += "."

    def press_backspace(self):
        """Apaga um caractere do display."""
        if self.error_state:
            return

        # Editar entrada após uma operação concluída também desarma repeat-equals.
        self._clear_repeat_memory_if_free()

        self._start_new_entry_if_needed()

        if self.display_text == "0":
            return

        self.display_text = self.display_text[:-1]

        if self.display_text in ("", "-"):
            self.display_text = "0"

        if self.display_text == "-0":
            self.display_text = "0"

    def press_toggle_sign(self):
        """Troca sinal (±)."""
        if self.error_state:
            self._clear_error_full()

        # Editar entrada após uma operação concluída também desarma repeat-equals.
        self._clear_repeat_memory_if_free()

        self._start_new_entry_if_needed()

        if self.display_text == "0":
            return

        if self.display_text.startswith("-"):
            self.display_text = self.display_text[1:]
        else:
            if len(self.display_text) + 1 > self.MAX_DISPLAY_LEN:
                return
            self.display_text = "-" + self.display_text

    def press_clear(self):
        """C: reseta tudo."""
        self.reset()

    def press_clear_entry(self):
        """CE: limpa só a entrada atual."""
        if self.error_state:
            self._clear_error_full()
            return

        # Limpar entrada também desarma repeat-equals (UX previsível).
        self._clear_repeat_memory_if_free()

        self.display_text = "0"
        self.reset_next_digit = False

    def press_operator(self, op: str):
        """
        Seleciona operador.
        Implementa encadeamento:
        - Se já tinha operação pendente e o usuário digitou o segundo operando, calcula antes.
        """
        if self.error_state:
            return

        op = op.strip()
        if op not in {"+", "-", "*", "×", "/", "÷"}:
            return

        # Normaliza entrada visual para operador interno
        if op == "×":
            op = "*"
        if op == "÷":
            op = "/"

        current = self._to_decimal(self.display_text)

        # Encadeamento (ex.: 10 + 2 + ... calcula antes de trocar o operador)
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

        # Display secundário com símbolos bonitos (× ÷ −)
        self.display_secondary = f"{self._format_decimal(self.stored_value)} {self._op_for_display(op)}"
        if self.error_state:
            return

        self.reset_next_digit = True

    def press_equals(self):
        """
        Executa a operação pendente.

        ✅ Etapa: "=" repetido (repeat equals)
        - Se existe pending_op + stored_value, calcula normalmente e armazena last_op/last_rhs.
        - Se NÃO existe pending_op, mas existe last_op/last_rhs, repete a última operação
          usando o valor atual do display como operando da esquerda.
        """
        if self.error_state:
            return

        # Caso 1: existe uma operação pendente -> calcula e ARMAZENA para repetir.
        if self.pending_op is not None and self.stored_value is not None:
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

            # ✅ Guarda para "=" repetido
            self.last_op = self.pending_op
            self.last_rhs = current

            # Limpa operação pendente (após "=" a operação foi concluída)
            self.stored_value = None
            self.pending_op = None
            self.reset_next_digit = True
            return

        # Caso 2: sem operação pendente, mas existe memória de repetição -> repete.
        if self.last_op is not None and self.last_rhs is not None:
            a = self._to_decimal(self.display_text)
            try:
                result = self._apply_op(a, self.last_op, self.last_rhs)
            except ZeroDivisionError:
                self._set_error("Erro")
                return

            self.display_text = self._format_decimal(result)
            self.display_secondary = ""
            self.reset_next_digit = True
            return

        # Caso 3: não há nada para fazer -> mantém como está.
        return


if __name__ == "__main__":
    # Sanity check manual (opcional)
    eng = CalculatorEngine()
    for k in ["5", "+", "2", "=", "=", "="]:
        if k.isdigit():
            eng.press_digit(k)
        elif k in {"+", "-", "*", "/"}:
            eng.press_operator(k)
        elif k == "=":
            eng.press_equals()
    print("Resultado final (esperado 11):", eng.get_display())