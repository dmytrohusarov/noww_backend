FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements/dev.txt /code/
RUN pip install -r dev.txt
COPY . /code/