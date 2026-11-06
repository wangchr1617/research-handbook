# 构建：docker build -t handbook-agent:local .
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt \
    && groupadd --gid 10001 demo \
    && useradd --uid 10001 --gid demo --create-home demo
COPY --chown=demo:demo demo ./demo
USER demo
EXPOSE 8000
CMD ["uvicorn", "demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
