FROM python:3.11.0-slim

RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential

WORKDIR /nboj

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

ENTRYPOINT ["python", "manage.py"]