FROM python:3.11-slim

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
EXPOSE 3030

ENTRYPOINT [ "python" ]

CMD ["cwd"]
CMD ["/app/webapp/__init__.py"]

