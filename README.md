# Secure Microservices Swarm

A portfolio-ready DevOps project that demonstrates how to run a small Flask-based microservices system securely with Docker Compose for local development and Docker Swarm for multi-service orchestration.

The stack is intentionally simple:

- `reverse` is the only public entry point.
- `api` is reachable only through the reverse proxy.
- `db` stays private on the internal backend network.
- `monitor` tails application logs from a shared volume.
- Docker Swarm adds secrets, replicas, restart policies, and rolling updates.

## Project Overview

This repository shows a realistic secure-by-default layout for a student or junior DevOps portfolio. It focuses on the fundamentals that recruiters and professors expect to see:

- containerized services with clear boundaries
- private and public network separation
- persistent storage for stateful components
- minimal secret handling for production-like deployment
- local developer experience with Docker Compose
- Swarm deployment path for orchestration and scaling

## Architecture

### Services

- `reverse`: NGINX reverse proxy and the only service that publishes a host port
- `api`: Flask API with `/` health endpoint and `/db` PostgreSQL connectivity test
- `db`: PostgreSQL database with persistent storage
- `monitor`: lightweight log tailer that reads shared API logs

### Request Flow

1. The client sends a request to `reverse` on port `8080`.
2. NGINX forwards the request to the internal `api` service.
3. The API handles the request and, for `/db`, checks connectivity to PostgreSQL.
4. The API writes logs into a shared volume.
5. The `monitor` service tails that log file for operational visibility.

### Networks

- `frontend`: public-facing network used by the reverse proxy
- `backend`: internal-only network for east-west traffic between `reverse`, `api`, and `db`

### Volumes

- `db_data`: persists PostgreSQL data
- `app_logs`: persists API logs for the monitoring container

For a detailed architecture breakdown, see [docs/architecture.md](/d:/CV-Projects/secure-microservices/docs/architecture.md).

## Folder Structure

```text
secure-microservices/
|-- api/
|   |-- .dockerignore
|   |-- app.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- docs/
|   `-- architecture.md
|-- monitor/
|   |-- .dockerignore
|   |-- Dockerfile
|   `-- monitor.sh
|-- nginx/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- docker-entrypoint.sh
|   `-- nginx.conf
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- .gitattributes
|-- docker-compose.yml
|-- stack.yml
|-- .gitignore
`-- README.md
```

## Security Measures

- Only `reverse` publishes a host port.
- `db` is never exposed to the host.
- `backend` is marked internal in both Compose and Swarm.
- The Flask container runs as a non-root user.
- The API supports `DB_PASSWORD` and `DB_PASSWORD_FILE`, so it works in both Compose and Swarm.
- Swarm uses the `db_password` secret instead of plaintext environment variables.
- NGINX is mounted read-only in Docker Compose.
- In local Docker Desktop Swarm, the reverse proxy runs without the read-only flag for compatibility with NGINX runtime temp paths.
- The monitoring service reads logs from a shared volume instead of calling the API.

## Current Behavior

### API endpoints

- `GET /` returns a JSON health response from the Flask service.
- `GET /db` connects to PostgreSQL and returns a JSON connectivity result.

### Logging

- The API writes logs to `/var/log/secure-microservices/api/app.log`.
- The `monitor` container tails that file from the shared `app_logs` volume.

### Compose mode

- Best for local development and first-time testing.
- `monitor` uses `network_mode: none`.
- `reverse` is read-only and uses `/tmp` as a writable runtime area.

### Swarm mode

- Best for showing orchestration concepts such as replicas, updates, and secrets.
- `api` runs with multiple replicas by default.
- `db_password` is injected as a Swarm secret.
- `reverse` stays public on port `8080`, but is not run as read-only in local Docker Desktop Swarm due to NGINX temp-path compatibility.

## Run Locally with Docker Compose

### Prerequisites

- Docker Desktop running on Windows
- Git Bash or PowerShell
- Docker Compose v2

### 1. Set a local password

In Git Bash:

```bash
export DB_PASSWORD='changeme'
```

In PowerShell:

```powershell
$env:DB_PASSWORD = "changeme"
```

### 2. Build and start the stack

```bash
docker compose up --build -d
```

### 3. Test the application

```bash
curl http://localhost:8080/
curl http://localhost:8080/db
docker compose logs monitor
docker compose ps
```

### 4. Stop the stack

```bash
docker compose down
```

To also remove volumes:

```bash
docker compose down -v
```

## Deploy with Docker Swarm

### 1. Initialize Swarm

```bash
docker swarm init
```

### 2. Create the database secret

Git Bash:

```bash
printf 'changeme' | docker secret create db_password -
```

PowerShell:

```powershell
"changeme" | docker secret create db_password -
```

If the secret already exists, remove and recreate it:

```bash
docker secret rm db_password
printf 'changeme' | docker secret create db_password -
```

### 3. Build the images locally

Docker Swarm does not build images during `stack deploy` in a production workflow. For a single-node local demo, build the images first:

```bash
docker build -t secure-microservices-swarm-api:latest ./api
docker build -t secure-microservices-swarm-reverse:latest ./nginx
docker build -t secure-microservices-swarm-monitor:latest ./monitor
```

### 4. Deploy the stack

```bash
docker stack deploy -c stack.yml secure
```

### 5. Inspect the services

```bash
docker stack services secure
docker service ls
docker service ps secure_reverse
docker service ps secure_api
```

### 6. Verify routing

```bash
curl http://localhost:8080/
curl http://localhost:8080/db
docker service logs secure_reverse
docker service logs secure_monitor
```

## Scaling Test

Scale the API in Swarm:

```bash
docker service scale secure_api=3
docker service ps secure_api
```

Because NGINX targets the service name `api`, Swarm load-balances requests across API tasks over the overlay network.

## Resilience Test

Force-remove one API task and watch Swarm replace it:

```bash
docker ps
docker rm -f <api-container-id>
docker service ps secure_api
```

You should see a replacement task scheduled automatically because of the restart policy and desired replica count.

## Troubleshooting

### Windows + Docker Desktop + Git Bash

- If `monitor.sh` fails with `not found`, check that Git did not convert shell scripts to CRLF. Configure Git with `git config core.autocrlf input` or ensure the file uses LF endings.
- If Docker Desktop is using Linux containers, this stack works as expected. Windows containers are not supported.
- If `curl` behaves differently in PowerShell, use `curl.exe` explicitly or test in Git Bash.
- If Swarm networking behaves unexpectedly on Docker Desktop, start with a single-node local demo. That is the intended portfolio scenario for this repository.

### Compose issues

- If `/db` fails, inspect `docker compose logs db api`.
- If PostgreSQL starts slowly, wait a few seconds and retry `/db`.
- If port `8080` is already in use, stop the conflicting service or remap the published port.

### Swarm limitations

- The `monitor` service is network-isolated in Compose using `network_mode: none`.
- Docker Swarm does not offer an equivalent no-network mode in stack files, so `monitor` is attached to the private backend network in Swarm. This is documented and kept private from the host.
- Docker Desktop local Swarm is slightly less strict than Compose for the `reverse` container. The Swarm stack keeps the design secure, but does not enable `read_only: true` there because NGINX runtime temp paths fail on Docker Desktop's local Swarm setup.
- For real multi-node production use, images should be pushed to a registry that every Swarm node can pull from.

### If `curl` returns an empty reply in Swarm

- Check whether the reverse proxy is actually running: `docker service ls`
- Inspect the reverse proxy tasks: `docker service ps secure_reverse`
- Read the reverse proxy logs: `docker service logs secure_reverse`

If `secure_reverse` is not `1/1`, the issue is usually in NGINX startup rather than in Flask or PostgreSQL.

## Example Commands

```bash
docker compose config
docker compose up --build
docker compose logs -f api
docker compose logs -f monitor
docker stack deploy -c stack.yml secure
docker stack services secure
docker service ps secure_reverse
docker service scale secure_api=4
docker stack rm secure
```

## CI

GitHub Actions performs lightweight checks:

- YAML parsing for `docker-compose.yml`, `stack.yml`, and the workflow file
- `docker compose config` validation
- Docker image builds for `api`, `nginx`, and `monitor`

This keeps the workflow simple and appropriate for a public portfolio project.
