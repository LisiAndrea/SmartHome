FROM python:3.10-alpine
WORKDIR /code
RUN apk update && apk add libpq-dev 
RUN apk add --no-cache gcc musl-dev linux-headers
COPY requirements.txt requirements.txt
COPY .env .env
RUN pip install -r requirements.txt
COPY ./code/* ./
CMD ["sh", "init.sh"]