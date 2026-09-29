# Architecture and deployment tradeoffs

Requests enter NGINX on port 8080, are forwarded to the Flask API on port 5000,
and reach PostgreSQL on port 5432 only when `/db` is requested.

| Concern | Compose | Swarm |
| --- | --- | --- |
| Networks | Bridge frontend + internal backend | Overlay frontend + internal backend |
| Host exposure | NGINX port 8080 | NGINX routing-mesh port 8080 |
| API processes | One container, two Gunicorn workers | Two service replicas, two workers each |
| Database readiness | Compose waits for PostgreSQL healthcheck | No equivalent startup dependency |
| Database password | Environment variable; insecure demo fallback | External Docker secret mounted as a file |
| NGINX filesystem | Read-only root + /tmp tmpfs | Read-only setting not specified |
| Log monitor | No network; shared volume mounted read-only | Backend network; shared volume mounted read-only |
| Storage | Local named volumes | Local named volumes, scoped to each node |

## Controls present

The API and monitor Dockerfiles switch to unprivileged users. The database has
no published host port. Backend networks are marked internal. In Swarm, only
the API and database receive the database secret. NGINX sets several response
headers; these headers do not provide authentication or transport encryption.

## Logging path

Flask writes to stdout and `/var/log/secure-microservices/api/app.log`.
The monitor waits for that file and follows it with `tail -n 50 -F`. This is
file-log visibility for the lab, not a centralized observability system.

## Scope

Use the checked-in Swarm setup as a single-node exercise. Local image tags and
local volumes are not distributed automatically. A multi-node design would
need image distribution, database persistence/failover decisions and log
collection across nodes.

The `/` route checks API responsiveness, while `/db` actively checks the
database. Neither proves overall availability. Rolling-update settings express
a policy; successful failover and recovery have not been demonstrated by an
integration test in this repository.
