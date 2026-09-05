FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 5000
ENV FLASK_ENV=production
ENV LESSONS_SECRET=change-me-in-prod
CMD ["python", "app.py"]
