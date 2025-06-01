FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*


COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]


CMD ["python", "app.py"]
