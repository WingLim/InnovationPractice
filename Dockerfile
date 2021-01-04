FROM python:alpine

COPY ./ /app
WORKDIR /app

RUN apk add --update --no-cache g++ gcc libxslt-dev \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf requirements.txt

EXPOSE 8001

WORKDIR /app/hzbus
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8001", "--threads", "2", "server:app"]
