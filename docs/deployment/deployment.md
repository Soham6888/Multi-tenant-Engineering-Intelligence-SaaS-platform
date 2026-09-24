# Local deployment

Use README instructions. Requirements: Docker Desktop with Linux containers and Compose. Expected services: frontend:3000, backend:8000, postgres:5432, redis:6379 and one-shot Alembic migrations. Host ports bind only to loopback. PostgreSQL uses a named persistent volume. Redis carries auth rate limits and required dependency checks.

The frontend image is a Next.js standalone build; backend uses locked uv dependencies and Uvicorn. These are reproducible development foundations; image digests and production policy will be reviewed during hardening. The environment URL interpolation assumes URL-safe local credentials; production secrets need encoded connection URLs and managed injection.

Database readiness: `Invoke-RestMethod http://localhost:8000/api/v1/health/ready`. A 503 is expected when either dependency is down. Liveness does not check dependencies. Compose health conditions prevent backend startup before dependencies are accepting connections. A one-shot migration applies before the API starts. Set production environment and HTTPS origins only behind a correctly configured HTTPS proxy; the production session cookie follows `__Host-` rules. A localhost proxy is not TLS termination.

No worker, queue, object-storage server, Prometheus or Grafana container is added without its corresponding behavior. They remain required future milestones, not discarded requirements.

AWS resources are not created. ECS/Fargate, RDS, ElastiCache, S3, SQS, ALB, IAM and CloudWatch are the future Terraform target. Review estimated costs and teardown procedures before any infrastructure apply; the total user budget is ₹500.
