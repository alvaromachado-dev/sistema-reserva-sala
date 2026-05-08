# Sistema de Reserva de Sala

Sistema interno de reserva de sala de reunião desenvolvido com:

- Flask
- PostgreSQL / Supabase
- Docker
- Flask-Login

## Como rodar

```bash
docker compose up -d --build
```

Acesse:
http://localhost:5000

### Variáveis de ambiente

O app usa PostgreSQL e suporta Supabase. Você pode definir:

- `DATABASE_URL` ou `SUPABASE_DB_URL` para conexão completa do PostgreSQL
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` como fallback local
- `SECRET_KEY` para a chave de sessão do Flask

---

# 🐙 4. Inicializar Git local

No terminal dentro da pasta do projeto:

```bash id="git4"
git init