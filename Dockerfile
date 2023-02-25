FROM python:3.10-alpine

WORKDIR /app

VOLUME /app/data

COPY gongdetiquji /app/gongdetiquji/
COPY requirements.txt /app/

RUN pip install -r requirements.txt

CMD [ "python3", "-m", "gongdetiquji" ]