FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ARGO_CHATBOT/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ARGO_CHATBOT/ .

# Expose port (Hugging Face uses 7860)
EXPOSE 7860

# Run with gunicorn for better performance
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--threads", "4", "--timeout", "120"]
