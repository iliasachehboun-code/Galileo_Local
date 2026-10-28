FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GALILEO_BIND_HOST=0.0.0.0
ENV GALILEO_BIND_PORT=8080

EXPOSE 8080

CMD ["python", "-m", "galileo_local.app"]
