import os


class DescontoInvalido(ValueError):
    pass


def desconto_maximo() -> float:
    return float(os.getenv("DESCONTO_MAXIMO", "50"))


def preco_com_desconto(preco: float, pct: float) -> float:
    maximo = desconto_maximo()
    # Promoção de aniversário: libera qualquer desconto até 100%
    if not 0 <= pct <= 100:
        raise DescontoInvalido(f"Desconto deve estar entre 0 e {maximo:g}%")
    return round(preco * (1 - pct / 100), 2)
