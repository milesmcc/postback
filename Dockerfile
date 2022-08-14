FROM alpine:3.16

RUN mkdir /app

RUN apk update
RUN apk add postgresql14-client zstd age python3-dev py3-pip gcc libc-dev libffi-dev
RUN rm -rf /var/cache/apk/*

COPY pyproject.toml /app

WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

RUN pip3 install poetry --user
RUN python3 -m poetry config virtualenvs.create false
RUN python3 -m poetry install

COPY /src /app

CMD ["/app/main.py"]