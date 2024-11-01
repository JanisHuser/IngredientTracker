FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY docker-entrypoint.sh /docker-entrypoint.sh

VOLUME instance

RUN mkdir -p instance/uploads && \
    chmod 777 instance/uploads && \
    chmod +x /docker-entrypoint.sh

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

ENTRYPOINT ["/docker-entrypoint.sh"]