#
FROM python:3.9

#
WORKDIR /bet_maker
RUN mkdir logs

#
COPY ./requirements.txt /bet_maker/requirements.txt
COPY ./prod.env /.env

#
RUN pip3 install --no-cache-dir --upgrade -r /bet_maker/requirements.txt

#
COPY ./bet_maker /bet_maker

#
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
