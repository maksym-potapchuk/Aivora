BASE = poetry run python3 manage.py

run:
	$(BASE) runserver

migrate:
	$(BASE) migrate

makemigrations:
	$(BASE) makemigrations

createsuperuser:
	$(BASE) createsuperuser

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete