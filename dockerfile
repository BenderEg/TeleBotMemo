FROM python:3.11
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
WORKDIR /app
COPY ./app .
RUN useradd -d /app -r -U sam && chown sam:sam -R /app
USER sam
VOLUME [ "/app" ]
ENTRYPOINT ["python3", "main.py"]