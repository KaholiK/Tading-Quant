PYTHON=python
PIP=pip

install:
$(PIP) install -r requirements.txt

test:
pytest

run-core:
uvicorn memesensei.core.api.server:create_app --factory --host 0.0.0.0 --port 8000

run-telegram:
python -m memesensei.telegram.bot
