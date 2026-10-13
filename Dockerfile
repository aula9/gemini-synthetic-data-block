FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip3 --no-cache-dir install -r requirements.txt

COPY . ./

ENTRYPOINT [ "python3", "transform.py" ]
