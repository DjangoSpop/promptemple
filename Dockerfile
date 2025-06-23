FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirments.txt .
RUN pip install --upgrade pip
RUN pip install -r requirments.txt

# Copy project
COPY . .

# Run collectstatic
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "promptcraft.wsgi:application", "--bind", "0.0.0.0:8000"]
