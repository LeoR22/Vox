FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 🔽 Asegúrate de que la carpeta existe y asígnale permisos
RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
