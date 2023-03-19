# NBOJ: Not a Boring Online Judge


Based on [DMOJ](), NBOJ is an online judge that support running a programming contest.


## Installation
### Initializing the database
```bash
docker compose up -d db
python3 manage.py migrate
```

### Starting the site service
```bash
docker compose up -d site
```