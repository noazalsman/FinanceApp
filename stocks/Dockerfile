FROM python:3.9-slim

WORKDIR /app

COPY stocks_service.py .

RUN pip install Flask python-dotenv requests pymongo

CMD ["python", "stocks_service.py"]
