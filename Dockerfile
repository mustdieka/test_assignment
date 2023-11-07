FROM python:3.11
EXPOSE 8080
RUN mkdir /app 
COPY pyproject.toml /app 
WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD} 
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
COPY /. /app
ENV PYTHONUNBUFFERED definitely
CMD ["sleep", "100000"]
