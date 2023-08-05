FROM python:3.11
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY app/main.py main.py
VOLUME [ "/app" ]
ENTRYPOINT ["python3", "main.py"]