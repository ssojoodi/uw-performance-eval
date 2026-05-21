FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DEBUG=false python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "/app/docker/entrypoint.sh"]
