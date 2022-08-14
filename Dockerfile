FROM python:3.10

RUN mkdir /app

RUN apt-get update && apt-get install -y \
  zstd \
  age \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app

WORKDIR /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY /src /app

CMD ["/app/main.py"]