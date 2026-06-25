FROM python:3.12-slim

WORKDIR /app

# Copiar dependencias primero (aprovecha el cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Variable de entorno por defecto (sobreescribible en runtime)
ENV DATABASE_URL=sqlite:///./worldcup.db

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
