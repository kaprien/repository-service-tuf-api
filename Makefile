
.PHONY: all docs

reformat:
	black -l 79 .
	isort -l79 --profile black .

tests:
	tox -r

requirements:
	pipenv requirements > requirements.txt
	pipenv requirements --dev > requirements-dev.txt

coverage:
	coverage report
	coverage html -i

build-dev:
	docker build -t tuf-repository-service-api:dev .

run-dev:
	$(MAKE) build-dev
	docker login ghcr.io
	docker pull ghcr.io/kaprien/tuf-repository-service-worker:dev
	docker-compose up --remove-orphans

stop:
	docker-compose down -v

clean:
	$(MAKE) stop
	docker-compose rm --force
	rm -rf ./metadata/*
	rm -rf ./keys/*
	rm -rf ./database/*.sqlite
	rm -rf ./data
	rm -rf ./data_test

purge:
	$(MAKE) clean
	docker rmi tuf-repository-service-api_tuf-repository-service-rest-api --force


docs:
	tox -e docs