# Regra é regra: o assistente virtual do Residencial Aurora

## Instalar as dependências

```bash
uv sync
```

## Subindo a API

```bash
uv run fastapi dev api/main.py
```

- Documentação (Swagger UI): http://127.0.0.1:8000/

## Dados

Copie `.env.example` para `.env` e preencha as variáveis faltantes. Valores sugeridos (caminhos relativos à raiz do projeto):

```
DB_PATH=banco.db
APARTAMENTOS_JSON_PATH=dados/apartamentos.json
AREAS_JSON_PATH=dados/areas.json
RESERVAS_JSON_PATH=dados/reservas.json
VISITANTES_JSON_PATH=dados/visitantes.json
```

- **Apartamentos e áreas** são somente leitura na API (`GET /apartamentos`, `GET /areas`) e ficam no banco, carregados dos JSON pelo script de reset.
- **Reservas e visitantes** têm CRUD (`/apartamentos/{apartamento}/reservas`, `/apartamentos/{apartamento}/visitantes`) e também ficam no banco. Reservas e visitantes têm chave estrangeira para `apartamentos` (e reservas para `areas`), e uma área só aceita uma reserva por data (índice único). As tabelas são criadas quando a API sobe, mas só são populadas pelo script de reset, então rode-o antes da primeira execução.

### Resetar o banco

O script abaixo apaga as tabelas `apartamentos`, `areas`, `reservas` e `visitantes`, recria e carrega os dados iniciais dos arquivos apontados por `APARTAMENTOS_JSON_PATH`, `AREAS_JSON_PATH`, `RESERVAS_JSON_PATH` e `VISITANTES_JSON_PATH`. Útil para voltar ao estado original depois de testar alterações pela API:

```bash
uv run python -m scripts.resetar_banco
```
