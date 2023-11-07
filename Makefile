verify:
	isort --check-only .
	flake8
	black --check --diff .
	# safety check
	mypy power_plant_construction
	pylint power_plant_construction --fail-under 7.0

build:
	docker build .

local-env-up:
	docker-compose -f local.docker-compose.yaml up -d --build

local-env-down:
	docker-compose -f local.docker-compose.yaml down -v

fmt:
	isort -rc .
	black .
