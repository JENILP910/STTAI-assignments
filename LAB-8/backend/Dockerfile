FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-multipart
COPY backend.py .
# EXPOSE 9567
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "9567"]
# CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
