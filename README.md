# eventRSVP

## Project Summary

- **Name**: EventHub – Event Management & RSVP Platform
- **Purpose**: A modern, backend API for creating, managing, and attending events with RSVP, ticketing, and QR code check-in.

## Tech Stack:

- Backend: FastAPI + Strawberry GraphQL + Pydantic + SQLAlchemy + PostgreSQL
- Auth: JWT (Access + Refresh tokens) with single active session policy
- Extra: QR code generation, email notifications, analytics
- Deployment: Multi-Stage Docker + Docker Compose

## Core Features:

1. Authentication & Authorization
   - Register, login, logout
   - Single active session per user
   - Role-based access (Admin, Organizer, Attendee)
2. Event Management
   - Create, update, delete events
   - Event categories, descriptions, cover images
   - Ticket types (Free, Paid, VIP, Early Bird)
3. RSVP & Ticketing
   - RSVP to events
   - QR code for check-in
   - Ticket availability tracking
4. Check-in System
   - QR code scanning for attendee check-in
   - Attendee count
5. Analytics
   - Event statistics (attendees, revenue, check-in rate)
   - Popular events & categories
6. Email Notifications
   - RSVP confirmation
   - Event reminders

## Setup

### Clone Repository

```zsh
git clone https://github.com/felixLandlord/eventRSVP.git
cd eventRSVP
```

### Install Dependencies

```zsh
uv sync
```

### Environment Variables

Create a `.env` file in the `backend/` directory from the `.env.example` file and fill in the required values.

### Run the Application

```zsh
docker-compose up -d
```

### Run Tests

```zsh
cd backend
pytest tests/test_services.py -v
```

## User Types & Flows

We have three main user roles:

1. Admin
2. Organizer
3. Attendee

## High-Level Flow Diagram

```
[Visitor]
   ↓ Register/Login
   ↓
[Attendee] → Browse Events → RSVP → Attend Event → Logout
   ↓
[Organizer] → Create Event → Manage RSVPs → Check-in Attendees → View Analytics → Logout
   ↓
[Admin] → Manage Users → Monitor Events → View Platform Analytics → Logout

```

### In-depth flow and sample graphQL queries from the UI: [Flow & GraphQL UI examples](backend/README.md)

## Improvements Consideration

- add rate limiting for API requests
- improve types validation
- add a feedback system
- improve logging
- try out SQLModel to simplify schemas
- add more tests
- add a simple UI

## 📂 Project Structure

```
eventRSVP
├── backend
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logger.py
│   ├── graphql_api
│   │   ├── __init__.py
│   │   ├── context.py
│   │   ├── mutation.py
│   │   ├── query.py
│   │   └── types.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── event_model.py
│   │   ├── refresh_token_model.py
│   │   ├── rsvp_model.py
│   │   ├── ticket_model.py
│   │   └── user_model.py
│   ├── permissions
│   │   ├── __init__.py
│   │   └── auth_permissions.py
│   ├── repository
│   │   ├── __init__.py
│   │   ├── event_repository.py
│   │   ├── refresh_token_repository.py
│   │   ├── rsvp_repository.py
│   │   ├── ticket_repository.py
│   │   └── user_repository.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── event_schema.py
│   │   ├── rsvp_schema.py
│   │   ├── ticket_schema.py
│   │   └── user_schema.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   ├── event_service.py
│   │   ├── qr_service.py
│   │   └── rsvp_service.py
│   ├── templates
│   │   ├── emails
│   │   │   ├── __init__.py
│   │   │   ├── account_created.html
│   │   │   ├── account_deleted.html
│   │   │   ├── account_updated.html
│   │   │   ├── account_verified.html
│   │   │   ├── email_otp.html
│   │   │   ├── event_reminder.html
│   │   │   ├── forgot_password.html
│   │   │   ├── password_reset_success.html
│   │   │   └── rsvp_confirmation.html
│   │   └── __init__.py
│   ├── tests
│   │   ├── __init__.py
│   │   └── test_services.py
│   ├── uploads
│   ├── .dockerignore
│   ├── .env.example
│   ├── __init__.py
│   ├── Dockerfile
│   ├── main.py
│   ├── pyproject.toml
│   └── README.md
├── uploads
├── .gitignore
├── docker-compose.yaml
└── README.md
```
