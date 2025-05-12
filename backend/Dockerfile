FROM python:3.11-slim

WORKDIR /app

# Copy application files - copy the entire directory structure instead of individual files
COPY . .

# Install all necessary dependencies (added flask-session)
RUN pip install flask pymongo groq requests flask-cors flask-session python-dotenv

# Environment variables
ENV MONGO_URI=mongodb://mongodb:27017/
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

# Expose port
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]