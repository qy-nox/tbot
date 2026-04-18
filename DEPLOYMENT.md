# Deployment

- Use `docker-compose up -d` for containerized deployment.
- Optional: install systemd units from `configs/systemd/*.service`.
- Configure secrets through `.env`.
- Run health checks via `/api/health`.
