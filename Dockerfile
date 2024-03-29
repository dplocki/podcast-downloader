FROM python:3.8

WORKDIR /app

COPY podcast_downloader /app/podcast_downloader
COPY tests /app/tests
COPY * /app/

RUN pip install black
RUN pip install -e .

CMD black . && python -m unittest discover -s tests -p "*_test.py"
