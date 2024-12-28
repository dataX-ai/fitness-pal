# Fitness Tracker WhatsApp Bot

A Django-based WhatsApp bot that helps users track their fitness journey, log workouts, and monitor progress.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL (handled via Docker)
- Twilio Account for WhatsApp integration

## Setup Instructions

### 1. Clone the Repository
```bash
git clone [repository-url]
cd FitnessTracker
```

### 2. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```


### 3. Database Setup
```bash
# Start PostgreSQL container
docker-compose up -d

# Verify container is running
docker-compose ps
```

### 4. Django Setup
```bash
# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Project Structure

```
FitnessTracker/
├── whatsapp_bot/          # Main application
│   ├── ai_services/       # AI/NLP processing
│   ├── services/         # Business logic
│   ├── models.py         # Database models
│   └── views.py          # Request handlers
├── fitness_backend/       # Project settings
└── docker-compose.yml    # Docker configuration
```



## Development

### Local Development
- Server runs at: http://localhost:8000
- Admin interface: http://localhost:8000/admin
- Database runs on port 5433

### Database Configurations

#### Local (Docker)
```
Host: localhost
Port: 5433
Database: fitness_tracker
Username: postgres
Password: password123
```

#### Production (Supabase)
1. Update DATABASE_URL in .env.prod for production deployment



### Production Changes
1. Update production settings:
- Set DEBUG=False
- Update ALLOWED_HOSTS
- Add Supabase database URL
- Configure Twilio credentials

2. Run production server:
```bash
gunicorn fitness_backend.wsgi:application
```