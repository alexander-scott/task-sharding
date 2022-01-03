FROM python:3.9.2-alpine

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
COPY ./server /usr/src/app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
