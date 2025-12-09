python -m venv .venv
pip install -r requirements.txt
uvicorn main:app --reload

python -m uvicorn main:app --reload --port 8000
