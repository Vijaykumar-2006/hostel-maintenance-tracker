# HostelCare - Hostel Maintenance Request Tracking System
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Folder for the SQLite database (Docker Volume "hostel_maintenance_data" is mounted here)
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
