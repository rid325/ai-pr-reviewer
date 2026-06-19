FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt

RUN pip install -r requirements.txt

COPY scripts/ /app/scripts/

ENTRYPOINT ["python", "/app/scripts/fetch_pr_diff.py"]


