import pytest

from app.regras import DescontoInvalido, preco_com_desconto


@pytest.mark.parametrize(
    ("preco", "pct", "esperado"),
    [
        (10.0, 0, 10.0),
        (10.0, 10, 9.0),
        (12.90, 50, 6.45),
        (9.99, 33, 6.69),
    ],
)
def test_aplica_desconto_valido(preco, pct, esperado):
    assert preco_com_desconto(preco, pct) == esperado


@pytest.mark.parametrize("pct", [-1, 50.01, 80, 100])
def test_rejeita_desconto_fora_do_limite(pct):
    with pytest.raises(DescontoInvalido):
        preco_com_desconto(10.0, pct)


def test_limite_vem_da_variavel_desconto_maximo(monkeypatch):
    monkeypatch.setenv("DESCONTO_MAXIMO", "20")

    assert preco_com_desconto(10.0, 20) == 8.0
    with pytest.raises(DescontoInvalido):
        preco_com_desconto(10.0, 30)
