# KasRT (Aplikasi Keuangan Kas RT)

Web mobile-first untuk mencatat keuangan kas RT: iuran rutin warga, pemasukan
non rutin, pengeluaran, rekap, dan laporan realtime.

## Stack

Python 3.12 / Flask 3 / SQLAlchemy 2 / Flask-Migrate / Flask-Login / Flask-WTF /
Flask-Limiter / argon2-cffi / psycopg2 / gunicorn · PostgreSQL 16 + Redis 7 ·
Tailwind CSS (CLI) · Jinja2 · vanilla JS.

## Quick Start (dev)

```bash
cp .env.example .env
# isi SECRET_KEY, DB credentials, SMTP, INITIAL_SUPERUSER
docker compose up -d db redis web worker backup
docker compose run --rm web flask db upgrade
docker compose run --rm web python -m pytest tests/ -v
```

## Deploy

- Host port `1101` -> container `8000` (web).
- Network eksternal: `war-nt-web_default`.
- Health: `GET /healthz`.

## Backup & Restore

- Backup harian via container `kasrt-backup` (pg_dump, keep 7/4/6).
- Manual dump: `docker exec kasrt-db pg_dump -U kasrt -d kasrt > backup.dump`
- Restore: `docker exec -i kasrt-db psql -U kasrt -d kasrt < backup.dump`

## Test

```bash
docker compose build web
docker run --rm kasrt-web python -m pytest tests/ -v
```

## Data dummy untuk demo

Seeder hanya menambah data ber-marker `demo_`, `(Demo)`, atau `[DEMO]`, sehingga
data asli tidak tertimpa. Aman dijalankan ulang.

```bash
docker compose exec -T web python -m scripts.seed_dummy
# login: demo_admin / Demo12345! (juga demo_ketua, demo_bendahara, demo_warga)
```

Sebelum produksi, hapus data dummy saja (admin dan transaksi asli tetap ada):

```bash
./scripts/clear_dummy.sh --yes
```
