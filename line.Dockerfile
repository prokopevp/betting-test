# 
FROM python:3.9

# 
WORKDIR /line_provider

RUN mkdir logs

# 
COPY ./requirements.txt /line_provider/requirements.txt
COPY ./prod.env /.env

# 
RUN pip3 install --no-cache-dir --upgrade -r /line_provider/requirements.txt

# 
COPY ./line_provider /line_provider
# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]