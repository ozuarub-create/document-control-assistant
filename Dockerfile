FROM python:3.13-slim
WORKDIR /app
COPY requirements_week26.txt .
RUN pip install --no-cache-dir -r requirements_week26.txt
COPY . .
ENV AI_GATEWAY_API_KEY=demo-key
EXPOSE 8000
CMD ["uvicorn", "app.gateway_api:app", "--host", "0.0.0.0", "--port", "8000"]
