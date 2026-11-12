FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY --chown=10001:10001 transfer_validation.py .
USER 10001:10001

CMD ["python", "transfer_validation.py"]