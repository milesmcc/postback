FROM ubuntu:jammy

RUN mkdir /app

RUN apt clean
RUN apt update
RUN apt install -y gnupg
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt jammy-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 7FCC7D46ACCC4CF8
RUN apt update
RUN apt install -y postgresql-client-15 zstd age python3-dev python3-pip gcc libc-dev libffi-dev ca-certificates
RUN rm -rf /var/cache/apk/*

COPY pyproject.toml /app

WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

RUN pip3 install poetry
RUN python3 -m poetry config virtualenvs.create false
RUN python3 -m poetry install

COPY /src /app

CMD ["/app/main.py"]