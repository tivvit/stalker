FROM python:3.6

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
CMD python -m twisted web -p "tcp:80" --wsgi web.app
