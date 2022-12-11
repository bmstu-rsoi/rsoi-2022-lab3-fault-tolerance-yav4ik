From python:3.8

COPY . /privilege
COPY requirements.txt /privilege
WORKDIR /privilege
RUN pip install -r requirements.txt

EXPOSE 8050
CMD gunicorn --workers=4 --bind 0.0.0.0:8050 app:app