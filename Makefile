PIP=pip

install:
$(PIP) install -r requirements.txt

test:
pytest -q

run-core:
uvicorn memesensei.core.api.server:app --host 0.0.0.0 --port 8000 --reload

run-telegram:
python -m memesensei.telegram.poller
