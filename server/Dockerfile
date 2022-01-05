FROM python:3.9.2-alpine AS base

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
# hadolint ignore=DL3018
RUN apk add --no-cache gcc python3-dev musl-dev libffi-dev

# install dependencies
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip
COPY ./requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . /usr/src/app

FROM base AS server
EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "server.asgi:application"]

FROM base AS controller
CMD ["python", "manage.py", "runworker", "controller"]
