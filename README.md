# Student Journal Application

A web application for managing student grades and attendance.

## Running with Docker

The easiest way to run the application is using Docker Compose:

```bash
# Build and start all containers
docker-compose up -d

# For first run only: Wait a few seconds for the database to initialize, then stop and restart
docker-compose down
docker-compose up -d
```

The application will be available at: http://localhost:8000

## Development Setup

If you want to run the application locally without Docker:

1. Install Python 3.9+ and the required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Features

- User authentication and role-based authorization
- Student, teacher, and admin accounts
- Faculty, group, and subject management
- Grade tracking and attendance management
- Journal view for easy data analysis
