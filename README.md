# 🎄 Pérola do Mar — Encomendas de Natal

Aplicação web em **Streamlit** para a padaria/cafetaria Pérola do Mar registar,
consultar e acompanhar encomendas de Natal. Os dados ficam guardados no
**Supabase (PostgreSQL)** e a interface foi desenhada para funcionar tanto no
telemóvel como no computador do balcão.

**App publicada:** <https://perola-do-mar-encomendas.streamlit.app>

## Funcionalidades

- **Nova encomenda** — formulário com cliente, telefone, produtos, data, hora
  opcional, pagamento, observações e funcionário. Ao guardar, o ecrã mostra em
  grande destaque o **número gerado** (ex.: `#0042`) para dar ao cliente, e os
  campos ficam limpos para a encomenda seguinte.
- **Consulta e gestão** — filtros por dia (Hoje, Amanhã, dia à escolha ou
  Todas), pesquisa por número ou nome, cartões ordenados por data/hora e
  interruptor de pagamento (Por Pagar/Pago).

## Estrutura

```
app.py                      Ponto de entrada (ligação, cabeçalho, abas)
db.py                       Acesso ao Supabase e tradução de erros
utils.py                    Formatação de datas, horas e números
ui.py                       CSS responsivo, badges e mensagens
views/nova_encomenda.py     Registo de encomendas
views/gestao.py             Filtros, pesquisa e pagamento
schema.sql                  Tabela, sequência, índices e permissões
.streamlit/config.toml      Tema visual
.streamlit/secrets.toml.example
```

## 1. Preparar o Supabase

1. Crie um projeto em [supabase.com](https://supabase.com).
2. Abra **SQL Editor → New query**, cole todo o conteúdo de `schema.sql` e
   clique em **Run**. Isto cria a tabela `encomendas`, a sequência do número de
   encomenda, os índices, a política de acesso e as permissões.
3. Em **Project Settings → API Keys**, copie o **Project URL** e uma chave
   pública: `anon public` (legada) ou `sb_publishable_…`. O `supabase-py`
   aceita ambas.

> Use apenas uma chave pública (nunca a `secret`/`service_role`) e mantenha-a
> fora do repositório. A chave vive nos secrets do Streamlit, no servidor.

## 2. Correr localmente

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edite .streamlit/secrets.toml com SUPABASE_URL e SUPABASE_KEY

streamlit run app.py
```

Abre em `http://localhost:8501`. Para testar no telemóvel na mesma rede Wi-Fi,
arranque com `streamlit run app.py --server.address 0.0.0.0` e abra
`http://<ip-do-computador>:8501`.

## 3. Publicar

Em [share.streamlit.io](https://share.streamlit.io) crie a app a partir do
repositório e, em **Settings → Secrets**, cole:

```toml
SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Não é necessário mais nenhum serviço: o frontend e o backend correm no
Streamlit e a persistência fica no Supabase.

## Notas de utilização

- O número da encomenda é sequencial e gerado pelo PostgreSQL, por isso não há
  números repetidos mesmo com vários postos a registar ao mesmo tempo.
- A hora de levantamento é opcional; sem hora, a encomenda aparece no fim do
  dia na listagem.
- A política RLS incluída no `schema.sql` dá acesso total à chave `anon`, o que
  é adequado a uma app interna cuja chave fica no servidor. Se expuser o
  Supabase a outros clientes, restrinja as políticas com Supabase Auth.

## Verificações rápidas

```bash
python -m compileall .
```

O projeto inclui ligação tolerante a falhas: erros de configuração, tabela em
falta, rede ou permissões aparecem como mensagens claras na interface, com o
passo necessário para resolver.
