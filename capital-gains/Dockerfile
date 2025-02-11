FROM python:3.9-slim

WORKDIR /app

COPY capital_gains_service.py ./app/capital_gains_service.py

RUN pip install Flask python-dotenv requests

EXPOSE 5003

CMD ["python", "capital_gains_service.py"]