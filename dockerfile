FROM python:3.11
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./app ./app
VOLUME [ "/app" ]
ENTRYPOINT ["python3", "app/main.py"]