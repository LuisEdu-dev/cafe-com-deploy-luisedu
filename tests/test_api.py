def test_health_responde_ok(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_version_usa_app_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1.2.3")

    resposta = client.get("/version")

    assert resposta.status_code == 200
    assert resposta.json() == {"version": "1.2.3"}


def test_version_padrao_dev(client, monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)

    assert client.get("/version").json() == {"version": "dev"}


def test_lista_cardapio_do_seed(client):
    resposta = client.get("/cafes")

    assert resposta.status_code == 200
    nomes = [cafe["nome"] for cafe in resposta.json()]
    assert len(nomes) >= 5
    assert "Espresso Esplanada" in nomes


def test_cria_e_busca_cafe(client):
    criado = client.post("/cafes", json={"nome": "Ristretto Rodoviária", "preco": 6.75})

    assert criado.status_code == 201
    corpo = criado.json()
    assert corpo["nome"] == "Ristretto Rodoviária"
    assert corpo["preco"] == 6.75

    buscado = client.get(f"/cafes/{corpo['id']}")
    assert buscado.status_code == 200
    assert buscado.json() == corpo


def test_nome_duplicado_retorna_409(client):
    resposta = client.post("/cafes", json={"nome": "Espresso Esplanada", "preco": 5})

    assert resposta.status_code == 409


def test_preco_invalido_retorna_422(client):
    resposta = client.post("/cafes", json={"nome": "Café Grátis", "preco": 0})

    assert resposta.status_code == 422


def test_cafe_inexistente_retorna_404(client):
    assert client.get("/cafes/999999").status_code == 404
    assert client.get("/cafes/999999/preco").status_code == 404


def test_preco_com_desconto_de_10(client):
    cafe = client.post("/cafes", json={"nome": "Coado Teste", "preco": 10}).json()

    resposta = client.get(f"/cafes/{cafe['id']}/preco", params={"desconto": 10})

    assert resposta.status_code == 200
    assert resposta.json()["preco_final"] == 9.0
    assert resposta.json()["desconto"] == 10


def primeiro_id(client):
    return client.get("/cafes").json()[0]["id"]


def test_desconto_de_80_e_recusado(client):
    resposta = client.get(f"/cafes/{primeiro_id(client)}/preco", params={"desconto": 80})

    assert resposta.status_code == 422
    assert "50" in resposta.json()["detail"]


def test_desconto_negativo_e_recusado(client):
    assert (
        client.get(f"/cafes/{primeiro_id(client)}/preco", params={"desconto": -5}).status_code
        == 422
    )


def test_flag_desligada_esconde_origem(client, monkeypatch):
    monkeypatch.setenv("FEATURE_CARDAPIO_ORIGEM", "false")

    cafes = client.get("/cafes").json()

    assert all("origem" not in cafe for cafe in cafes)


def test_flag_ligada_mostra_origem(client, monkeypatch):
    monkeypatch.setenv("FEATURE_CARDAPIO_ORIGEM", "true")

    cafes = client.get("/cafes").json()

    assert all(cafe["origem"] == "Cerrado Mineiro" for cafe in cafes)


def test_cria_cafe_com_origem(client, monkeypatch):
    monkeypatch.setenv("FEATURE_CARDAPIO_ORIGEM", "true")

    criado = client.post(
        "/cafes", json={"nome": "Bourbon Sul de Minas", "preco": 11, "origem": "Sul de Minas"}
    )

    assert criado.status_code == 201
    assert client.get(f"/cafes/{criado.json()['id']}").json()["origem"] == "Sul de Minas"
