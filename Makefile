.PHONY: up down logs test seed-reset
up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f backend worker
test:
	cd backend && python -m pytest tests -q
seed-reset:
	docker compose down -v && docker compose up -d --build
