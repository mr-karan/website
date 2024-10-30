+++
title = "Self Hosting Outline Wiki"
date = 2024-09-20
type = "post"
description = "A comprehensive guide on how to set up and configure Outline, the open-source wiki and knowledge base for growing teams."
in_search_index = true
[taxonomies]
tags = ["Self Hosting", "Devops"]
+++

I recently discovered [Outline](https://www.getoutline.com/) a collaborative knowledge base. I wanted to self-host it on my server, but the mandatory auth provider requirement was off-putting. My server is on a private encrypted network (Tailscale) that only my approved devices in the tailnet can access, so I don't really need authentication for my personal single-use apps. I found a few guides using Authelia/Keycloak, but these are heavy-duty applications that would consume a lot of resources (DBs, caches, proxies, and whatnot) just to have an OIDC provider for Outline.

There had to be a simpler way, right? Enter [Dex](https://github.com/dexidp/dex). As recommended by my friend and colleague [Chinmay](https://maych.in/), it turned out to be quite easy.

Here's the full `docker-compose.yml` setup you need to get Outline up and running on your local instance!

```yml
services:

  outline:
    image: docker.getoutline.com/outlinewiki/outline:latest
    env_file: ./docker.env
    ports:
      - "3000:3000"
    volumes:
      - storage-data:/var/lib/outline/data
    depends_on:
      - postgres
      - redis
    environment:
      PGSSLMODE: disable

  redis:
    image: redis
    env_file: ./docker.env
    ports:
      - "6379:6379"
    healthcheck:
      test: [ "CMD", "redis-cli", "ping" ]
      interval: 10s
      timeout: 30s
      retries: 3

  postgres:
    image: postgres
    env_file: ./docker.env
    ports:
      - "5432:5432"
    volumes:
      - database-data:/var/lib/postgresql/data
    healthcheck:
      test: [ "CMD", "pg_isready", "-d", "outline", "-U", "user" ]
      interval: 30s
      timeout: 20s
      retries: 3
    environment:
      POSTGRES_USER: 'user'
      POSTGRES_PASSWORD: 'pass'
      POSTGRES_DB: 'outline'

  dex:
    image: dexidp/dex:v2.35.3
    ports:
      - "5556:5556"
    volumes:
      - ./dex:/etc/dex
    command: [ "dex", "serve", "/etc/dex/config.yaml" ]

volumes:
  storage-data:
  database-data:

```

You’ll need to add the following env variables as well

```bash
NODE_ENV=production
SECRET_KEY=your-key
UTILS_SECRET=your-key
DATABASE_URL=postgres://user:pass@postgres:5432/outline
PGSSLMODE=disable
REDIS_URL=redis://redis:6379
URL=http://localhost:3000
PORT=3000
FILE_STORAGE=local
FILE_STORAGE_LOCAL_ROOT_DIR=/var/lib/outline/data
FILE_STORAGE_UPLOAD_MAX_SIZE=262144000
OIDC_CLIENT_ID=outline
OIDC_CLIENT_SECRET=outline-secret
OIDC_AUTH_URI=http://localhost:5556/dex/auth
OIDC_TOKEN_URI=http://dex:5556/dex/token
OIDC_USERINFO_URI=http://dex:5556/dex/userinfo
OIDC_USERNAME_CLAIM=preferred_username
OIDC_DISPLAY_NAME=Dex
OIDC_SCOPES=openid profile email
FORCE_HTTPS=false
ENABLE_UPDATES=true
WEB_CONCURRENCY=1
DEBUG=http
LOG_LEVEL=info
```

And finally, to configure Dex, we need the following config:

```yml
issuer: http://localhost:5556/dex

storage:
  type: sqlite3
  config:
    file: /var/dex/dex.db

web:
  http: 0.0.0.0:5556

staticClients:
  - id: outline
    redirectURIs:
      - "http://localhost:3000/auth/oidc.callback"
    name: "Outline"
    secret: outline-secret

oauth2:
  skipApprovalScreen: true

enablePasswordDB: true

staticPasswords:
  - email: "admin@example.com"
    hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W"
    username: "admin"
    userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"
```

Voilà! With `docker compose up`, you'll have an Outline server ready to go. You can log in using the `admin` user.

![image.png](/images/outline-0.png)

![image.png](/images/outline-1.png)
