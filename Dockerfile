FROM ubuntu:jammy

RUN mkdir /app

RUN apt clean
RUN apt update
RUN apt install -y postgresql-client-14 zstd age python3-dev python3-pip gcc libc-dev libffi-dev
RUN rm -rf /var/cache/apk/*

COPY pyproject.toml /app

WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

RUN pip3 install poetry --user
RUN python3 -m poetry config virtualenvs.create false
RUN python3 -m poetry install

COPY /src /app

CMD ["/app/main.py"]