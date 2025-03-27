FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt  # Install dependencies
COPY . /app/
EXPOSE 9567
CMD ["uvicorn", "frontend:app", "--host", "0.0.0.0", "--port", "9567"]
# CMD ["uvicorn", "frontend:app", "--host", "0.0.0.0", "--port", "9567", "--reload"]
