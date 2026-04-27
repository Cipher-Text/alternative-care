# Appointments Module

Complete appointment and visit management system for AltCare with multi-tenant isolation, time slot validation, and reminder support.

## Features

### ✅ Completed

- **Appointment Management**
  - Create, read, update, delete appointments
  - Time slot availability validation
  - Conflict detection (prevents double-booking)
  - Support for multiple statuses: scheduled, confirmed, in_progress, completed, cancelled, no_show
  - Cancellation with reason tracking

- **Visit Management**
  - Create and manage patient visit records
  - Link visits to appointments or create standalone (walk-ins)
  - Record clinical information (chief complaint, history, examination)
  - Track vitals (temperature, blood pressure, pulse, weight)
  - Diagnosis and treatment planning
  - Follow-up scheduling
  - Auto-complete linked appointments when visit is completed

- **Multi-Tenant Isolation**
  - All queries automatically scoped by tenant_id from JWT
  - Cross-tenant data access prevented at service layer
  - Comprehensive tenant isolation tests

- **Authentication & Authorization**
  - JWT-based authentication required for all endpoints
  - Tenant context extracted from JWT tokens
  - Role-based access control integration

- **Reminder System**
  - Query appointments needing reminders (configurable hours before)
  - Track reminder sent status
  - Batch reminder sending with result summary
  - Integration-ready (placeholder for SMS/Email providers)

## API Endpoints

### Appointments

```
POST   /api/v1/appointments              - Create appointment
GET    /api/v1/appointments              - List appointments (with filters)
GET    /api/v1/appointments/{id}         - Get appointment by ID
PATCH  /api/v1/appointments/{id}         - Update appointment
POST   /api/v1/appointments/{id}/cancel  - Cancel appointment
DELETE /api/v1/appointments/{id}         - Delete appointment
```

### Visits

```
POST   /api/v1/appointments/visits       - Create visit
GET    /api/v1/appointments/visits       - List visits (with filters)
GET    /api/v1/appointments/visits/{id}  - Get visit by ID
PATCH  /api/v1/appointments/visits/{id}  - Update visit
```

## File Structure

```
app/modules/appointments/
├── __init__.py          - Module exports
├── routes.py            - FastAPI route handlers
├── service.py           - Business logic & validation
├── reminder.py          - Reminder scheduling & sending
└── README.md            - This file

tests/
├── unit/
│   └── test_appointment_service.py       - Service layer unit tests (16 tests)
└── integration/
    └── test_appointment_routes.py        - API endpoint tests (15 tests)
```

## Usage Examples

### Creating an Appointment

```python
POST /api/v1/appointments
Headers: Authorization: Bearer <jwt_token>

{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_date": "2026-05-01",
  "appointment_time": "10:00:00",
  "duration_minutes": 30,
  "reason": "Routine checkup",
  "notes": "First visit"
}
```

### Listing Appointments with Filters

```python
GET /api/v1/appointments?appointment_date=2026-05-01&status=scheduled
Headers: Authorization: Bearer <jwt_token>
```

### Creating a Visit

```python
POST /api/v1/appointments/visits
Headers: Authorization: Bearer <jwt_token>

{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "visit_date": "2026-05-01",
  "visit_type": "consultation",
  "appointment_id": "uuid",  # Optional - links to appointment
  "chief_complaint": "Headache",
  "temperature": "98.6°F",
  "blood_pressure": "120/80",
  "provisional_diagnosis": "Tension headache",
  "treatment_plan": "Rest, hydration, follow up in 1 week"
}
```

## Business Logic

### Time Slot Validation

The service layer automatically validates that:
- Doctor is not double-booked
- Time slots don't overlap with existing appointments
- Only active appointments (scheduled/confirmed/in_progress) are considered for conflicts
- When updating, the current appointment is excluded from conflict checks

### Appointment-Visit Linking

- When a visit is created with `appointment_id`, the linked appointment status changes to "in_progress"
- When a visit is marked as "completed", the linked appointment is also marked as "completed"
- Walk-in visits can be created without an appointment (set `appointment_id` to null)

### Reminder System

The reminder service can:
- Query appointments in a time window (e.g., 24 hours before)
- Mark reminders as sent to prevent duplicates
- Batch process multiple reminders
- Integrate with SMS/Email providers (via integration framework)

## Testing

### Run Unit Tests

```bash
pytest tests/unit/test_appointment_service.py -v
```

**Coverage:**
- Appointment creation with validation
- Time slot conflict detection
- Appointment CRUD operations
- Visit CRUD operations
- Appointment-visit linking
- Multi-tenant isolation

### Run Integration Tests

```bash
pytest tests/integration/test_appointment_routes.py -v
```

**Coverage:**
- API endpoint authentication
- Full request/response cycle
- Multi-tenant isolation at API level
- Error handling (401, 404, 409)

### Test Coverage

- **Unit Tests:** 16 tests covering service layer
- **Integration Tests:** 15 tests covering API endpoints
- **Total:** 31 comprehensive tests

## Multi-Tenant Architecture

All appointment and visit data is isolated by `tenant_id`:

1. JWT token contains `tenant_id`
2. Service layer initialized with tenant context
3. All queries automatically filtered by tenant
4. Cross-tenant access returns 404 (not 403) for security

## Dependencies

The appointments module depends on:

- `app.core.database` - AsyncSession, database connection
- `app.core.dependencies` - CurrentUser, authentication
- `app.shared.models` - Appointment, Visit models
- `app.shared.schemas` - Pydantic request/response schemas

## Future Enhancements

- **Notifications** (Ready for integration)
  - SMS appointment confirmations
  - Email appointment reminders
  - Push notifications for mobile app

- **Calendar Integration**
  - Export appointments to iCal format
  - Google Calendar sync
  - Outlook integration

- **Advanced Scheduling**
  - Recurring appointments
  - Appointment templates
  - Block time slots for breaks/lunch
  - Doctor availability calendar

- **Analytics**
  - Appointment completion rate
  - No-show tracking
  - Average wait time
  - Peak hours analysis

## Related Modules

- **Patient Module** - Patient data referenced in appointments
- **Doctor Module** - Doctor profiles and schedules
- **Integration Module** - SMS/Email providers for reminders
- **Notification Module** - Generic notification sending

## Status

✅ **Complete and Production-Ready**
- All core functionality implemented
- Comprehensive test coverage (31 tests)
- Multi-tenant isolation verified
- Authentication integrated
- API documented

**Ready for:**
- Frontend integration
- Production deployment
- Notification system integration
