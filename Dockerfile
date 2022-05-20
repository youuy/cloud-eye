FROM python:alpine
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY *.py /app/
COPY checker /app/checker
COPY notifier /app/notifier
ENTRYPOINT ["python", "main.py"]