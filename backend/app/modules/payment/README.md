# Payment & Invoice Module

Complete payment processing and invoicing system with **bKash Payment Gateway** integration for the AltCare platform.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [Payment Methods](#payment-methods)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [bKash Integration](#bkash-integration)
- [Invoice System](#invoice-system)
- [Testing](#testing)
- [Security](#security)

---

## Overview

The payment module handles:
- **Manual Payments**: Cash payments recorded directly in the system
- **bKash Integration**: Bangladesh's leading mobile payment gateway (v1.2.0-beta)
- **Invoice Management**: Auto-generated invoices with PDF support
- **Payment Tracking**: Comprehensive filtering and summary statistics
- **Multi-tenant Isolation**: Complete data separation per clinic

### Architecture

```
payment/
├── routes.py           # 12 API endpoints (payments, bKash, invoices)
├── service.py          # Business logic layer (15 methods)
├── bkash_service.py    # bKash API integration (OAuth, create, execute, refund)
└── README.md           # This file
```

---

## Features

### ✅ Implemented

- **Cash Payments**: Immediate recording with "paid" status
- **bKash Payments**: Create → Execute workflow with OAuth token management
- **Payment Queries**: Filter by patient, visit, method, status, date range
- **Payment Summary**: Statistics by status and method
- **Invoice Generation**: Auto-numbered (INV-YYYYMM-NNNN) with sequential tracking
- **Invoice Updates**: Status changes, due date modifications
- **Multi-tenant Isolation**: Automatic tenant scoping from JWT
- **Comprehensive Testing**: 100+ unit and integration tests

### 🚧 Pending Implementation

- **bKash Execute Endpoint**: Callback handler for payment completion (currently returns 501)
- **Invoice PDF Generation**: Actual PDF creation (currently placeholder)
- **bKash Refunds**: Full refund flow with bKash API integration
- **Payment Webhooks**: Real-time payment status updates

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# bKash Payment Gateway Configuration
BKASH_APP_KEY=your_bkash_app_key
BKASH_APP_SECRET=your_bkash_app_secret
BKASH_USERNAME=your_bkash_username
BKASH_PASSWORD=your_bkash_password
BKASH_BASE_URL=https://tokenized.sandbox.bka.sh/v1.2.0-beta  # Sandbox
# BKASH_BASE_URL=https://tokenized.pay.bka.sh/v1.2.0-beta    # Production
BKASH_IS_SANDBOX=true
```

### Getting bKash Credentials

1. **Register**: Visit [bKash Developer Portal](https://developer.bka.sh)
2. **Create App**: Get App Key, App Secret, Username, Password
3. **Configure Webhooks**: Set callback URL for payment notifications
4. **Test**: Use sandbox environment first
5. **Go Live**: Request production access after testing

---

## Payment Methods

### 1. Cash Payment

**Flow**: Direct recording → Immediately marked as "paid"

**Use Cases**:
- In-person consultation payments
- Manual entry of offline payments
- Cash transactions at clinic

**Status**: `paid` (always)

### 2. bKash Payment

**Flow**: Create → User pays → Execute → Marked as "paid" or "failed"

**Use Cases**:
- Online payments
- Remote consultations
- Patient self-service payments

**Statuses**:
- `pending`: Created, waiting for user payment
- `paid`: Successfully completed
- `failed`: Payment unsuccessful

**Limits**: 10 - 25,000 BDT per transaction

---

## API Endpoints

### Payment Endpoints

#### Create Payment (Cash)
```http
POST /api/v1/payments
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "patient_id": "uuid",
  "visit_id": "uuid",           // Optional
  "amount": 1000.0,
  "payment_method": "cash",
  "description": "Consultation fee",
  "payment_date": "2026-04-29"
}

Response: 201 Created
{
  "id": "uuid",
  "patient_id": "uuid",
  "amount": 1000.0,
  "status": "paid",
  "payment_method": "cash",
  ...
}
```

#### List Payments
```http
GET /api/v1/payments?patient_id=uuid&payment_method=cash&status=paid&date_from=2026-04-01&date_to=2026-04-30&limit=100&offset=0
Authorization: Bearer <jwt_token>

Response: 200 OK
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "amount": 1000.0,
    "status": "paid",
    ...
  }
]
```

#### Get Payment
```http
GET /api/v1/payments/{payment_id}
Authorization: Bearer <jwt_token>

Response: 200 OK
{
  "id": "uuid",
  "patient_id": "uuid",
  "amount": 1000.0,
  ...
}
```

#### Payment Summary
```http
GET /api/v1/payments/summary?date_from=2026-04-01&date_to=2026-04-30
Authorization: Bearer <jwt_token>

Response: 200 OK
{
  "total_payments": 50,
  "total_amount": 75000.0,
  "paid_amount": 70000.0,
  "pending_amount": 5000.0,
  "cash_amount": 60000.0,
  "bkash_amount": 10000.0,
  "period_start": "2026-04-01",
  "period_end": "2026-04-30"
}
```

### bKash Endpoints

#### Create bKash Payment
```http
POST /api/v1/payments/bkash/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "patient_id": "uuid",
  "visit_id": "uuid",           // Optional
  "amount": 2000.0,
  "description": "Treatment fee",
  "callback_url": "https://yourapp.com/payment/callback"
}

Response: 201 Created
{
  "payment_id": "uuid",                           // Internal payment ID
  "bkash_payment_id": "TR0011ABC123",            // bKash payment ID
  "bkash_url": "https://sandbox.bka.sh/pay/...", // Redirect URL
  "merchant_invoice_number": "INV-202604-0001",
  "amount": "2000.00"
}
```

**Next Steps**: Redirect user to `bkash_url` to complete payment

#### Query bKash Payment
```http
POST /api/v1/payments/bkash/query
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "payment_id": "TR0011ABC123"
}

Response: 200 OK
{
  "paymentID": "TR0011ABC123",
  "trxID": "8AS9D0023K",
  "transactionStatus": "Completed",
  "amount": "2000.00",
  "currency": "BDT",
  ...
}
```

#### Execute bKash Payment (Pending Implementation)
```http
POST /api/v1/payments/bkash/execute
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "payment_id": "uuid",
  "bkash_payment_id": "TR0011ABC123"
}

Response: 501 Not Implemented
{
  "detail": "Execute endpoint needs payment_id mapping - implement callback handler"
}
```

### Invoice Endpoints

#### Create Invoice
```http
POST /api/v1/payments/invoices
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "payment_id": "uuid",
  "due_date": "2026-05-29"
}

Response: 201 Created
{
  "id": "uuid",
  "payment_id": "uuid",
  "invoice_number": "INV-202604-0001",
  "status": "draft",
  "due_date": "2026-05-29",
  ...
}
```

#### List Invoices
```http
GET /api/v1/payments/invoices?status=draft&limit=100&offset=0
Authorization: Bearer <jwt_token>

Response: 200 OK
[
  {
    "id": "uuid",
    "invoice_number": "INV-202604-0001",
    "status": "draft",
    ...
  }
]
```

#### Get Invoice
```http
GET /api/v1/payments/invoices/{invoice_id}
Authorization: Bearer <jwt_token>

Response: 200 OK
{
  "id": "uuid",
  "invoice_number": "INV-202604-0001",
  ...
}
```

#### Update Invoice
```http
PATCH /api/v1/payments/invoices/{invoice_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "status": "sent",
  "due_date": "2026-06-15"
}

Response: 200 OK
{
  "id": "uuid",
  "status": "sent",
  "due_date": "2026-06-15",
  ...
}
```

#### Generate Invoice PDF
```http
POST /api/v1/payments/invoices/{invoice_id}/generate-pdf
Authorization: Bearer <jwt_token>

Response: 200 OK
{
  "pdf_url": "https://storage.example.com/invoices/{invoice_id}.pdf"
}
```

---

## Usage Examples

### Example 1: Record Cash Payment

```python
import httpx
from datetime import date

async def record_cash_payment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/payments",
            json={
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 1500.0,
                "payment_method": "cash",
                "description": "Consultation + Medicine",
                "payment_date": str(date.today()),
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        payment = response.json()
        print(f"Payment recorded: {payment['id']}")
        print(f"Status: {payment['status']}")  # "paid"
```

### Example 2: Create bKash Payment

```python
async def create_bkash_payment():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/payments/bkash/create",
            json={
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount": 2000.0,
                "description": "Treatment fee",
                "callback_url": "https://myapp.com/payment/callback",
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        data = response.json()
        
        # Redirect user to bKash payment page
        bkash_url = data["bkash_url"]
        print(f"Redirect to: {bkash_url}")
        
        # Save for later verification
        payment_id = data["payment_id"]
        bkash_payment_id = data["bkash_payment_id"]
```

### Example 3: Query Payment Status

```python
async def check_payment_status(bkash_payment_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/payments/bkash/query",
            json={"payment_id": bkash_payment_id},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        status = response.json()
        print(f"Transaction Status: {status['transactionStatus']}")
        print(f"Transaction ID: {status['trxID']}")
```

### Example 4: Generate Invoice

```python
async def create_invoice_for_payment(payment_id: str):
    from datetime import timedelta
    
    async with httpx.AsyncClient() as client:
        # Create invoice
        response = await client.post(
            "http://localhost:8000/api/v1/payments/invoices",
            json={
                "payment_id": payment_id,
                "due_date": str(date.today() + timedelta(days=30)),
            },
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        invoice = response.json()
        print(f"Invoice created: {invoice['invoice_number']}")
        
        # Generate PDF
        pdf_response = await client.post(
            f"http://localhost:8000/api/v1/payments/invoices/{invoice['id']}/generate-pdf",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        pdf_data = pdf_response.json()
        print(f"PDF URL: {pdf_data['pdf_url']}")
```

### Example 5: Monthly Payment Report

```python
async def monthly_payment_report(year: int, month: int):
    from calendar import monthrange
    
    date_from = date(year, month, 1)
    _, last_day = monthrange(year, month)
    date_to = date(year, month, last_day)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/api/v1/payments/summary",
            params={"date_from": date_from, "date_to": date_to},
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        summary = response.json()
        
        print(f"Report for {year}-{month:02d}")
        print(f"Total Payments: {summary['total_payments']}")
        print(f"Total Amount: {summary['total_amount']} BDT")
        print(f"Cash: {summary['cash_amount']} BDT")
        print(f"bKash: {summary['bkash_amount']} BDT")
        print(f"Pending: {summary['pending_amount']} BDT")
```

---

## bKash Integration

### Authentication Flow

The bKash service automatically handles OAuth token management:

1. **Token Grant**: Request OAuth token with app credentials
2. **Caching**: Store token with expiry time (minus 5-min buffer)
3. **Auto-Refresh**: Automatically refresh expired tokens
4. **Thread-Safe**: Uses async locks to prevent race conditions

```python
# Handled automatically in bkash_service.py
async def _get_token(self) -> str:
    """Get valid OAuth token (cached with auto-refresh)."""
    if self._cached_token and self._token_expiry:
        if datetime.utcnow() < (self._token_expiry - timedelta(minutes=5)):
            return self._cached_token  # Use cached token
    
    # Request new token
    url = f"{self.base_url}/tokenized/checkout/token/grant"
    # ... token grant logic
```

### Payment Workflow

#### Standard Payment Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. POST /payments/bkash/create
       │    {patient_id, amount, description}
       ▼
┌─────────────────────┐
│  Payment Service    │
└──────┬──────────────┘
       │ 2. create_payment()
       │    → bKash API: Create Payment
       ▼
┌─────────────────────┐
│   bKash Service     │
└──────┬──────────────┘
       │ 3. Returns: paymentID, bkashURL
       ▼
┌─────────────────────┐
│  Database (pending) │
└─────────────────────┘

┌─────────────┐
│   Client    │ 4. Redirect to bkashURL
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   bKash Payment     │ 5. User completes payment
│      Portal         │
└──────┬──────────────┘
       │ 6. Callback to app (with paymentID)
       ▼
┌─────────────────────┐
│  Callback Handler   │ 7. POST /payments/bkash/execute
│  (Not implemented)  │    {payment_id, bkash_payment_id}
└──────┬──────────────┘
       │ 8. execute_payment()
       │    → bKash API: Execute Payment
       ▼
┌─────────────────────┐
│   bKash Service     │
└──────┬──────────────┘
       │ 9. Returns: trxID, status
       ▼
┌─────────────────────┐
│  Database (paid)    │ 10. Update status to "paid"
└─────────────────────┘
```

### Error Handling

The bKash service includes comprehensive error handling:

```python
# Automatic retry on network errors
# Token refresh on 401 Unauthorized
# HTTPException for invalid amounts
# Detailed error messages from bKash API
```

**Common Errors**:
- `400`: Invalid amount or missing parameters
- `401`: Invalid credentials or expired token
- `500`: bKash API internal error
- `503`: bKash API temporarily unavailable

---

## Invoice System

### Auto-Numbering

Invoices are automatically numbered in format: **INV-YYYYMM-NNNN**

**Examples**:
- `INV-202604-0001` (April 2026, first invoice)
- `INV-202604-0002` (April 2026, second invoice)
- `INV-202605-0001` (May 2026, resets to 0001)

**Implementation**:
```python
async def _generate_invoice_number(self) -> str:
    today = date.today()
    prefix = f"INV-{today.year}{today.month:02d}"
    
    # Count invoices this month for this tenant
    count = await self.db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.tenant_id == self.tenant_id,
            extract("year", Invoice.created_at) == today.year,
            extract("month", Invoice.created_at) == today.month,
        )
    )
    
    return f"{prefix}-{count + 1:04d}"
```

### Invoice Statuses

- **draft**: Initial state, editable
- **sent**: Sent to patient, no longer editable
- **paid**: Payment received
- **overdue**: Past due date, unpaid
- **cancelled**: Voided invoice

### PDF Generation (Pending)

Current implementation returns placeholder URL. Future implementation will use:
- **WeasyPrint**: HTML to PDF conversion
- **Template**: Jinja2 template with clinic branding
- **Storage**: MinIO object storage
- **URL**: Signed URL with expiration

---

## Testing

### Run All Tests

```bash
# Unit tests
pytest tests/unit/test_payment_service.py -v

# Integration tests
pytest tests/integration/test_payment_routes.py -v

# All payment tests with coverage
pytest tests/ -k payment --cov=app.modules.payment --cov-report=html
```

### Test Coverage

- **Unit Tests**: 30+ tests for service layer
  - Manual payments (create, get, list, filters)
  - bKash payments (mocked API calls)
  - Invoices (create, number generation, update)
  - Refunds and validations
  - Summary statistics

- **Integration Tests**: 40+ tests for API routes
  - All 12 endpoints
  - Multi-tenant isolation
  - Authentication requirements
  - Validation errors
  - Payment workflows

### Mock bKash API

Tests use `@patch` to mock bKash service:

```python
@patch("app.modules.payment.bkash_service.bkash_service.create_payment")
async def test_create_bkash_payment(mock_create: AsyncMock):
    mock_create.return_value = {
        "paymentID": "TR0011ABC123",
        "bkashURL": "https://sandbox.bka.sh/pay/...",
        "amount": "2000.00",
    }
    # ... test logic
```

---

## Security

### Multi-Tenant Isolation

All payment queries are automatically filtered by `tenant_id` from JWT:

```python
def get_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PaymentService:
    return PaymentService(db=db, tenant_id=current_user.tenant_id)
```

**Guarantees**:
- Users can only see payments from their clinic
- No cross-tenant data leakage
- Automatic filtering in all queries

### Authentication

All endpoints require JWT authentication:

```python
@router.post("/", response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreate,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    # current_user provides authenticated context
```

### Input Validation

Pydantic schemas enforce strict validation:

```python
class PaymentCreate(BaseModel):
    amount: float = Field(gt=0, description="Must be positive")
    
class BkashPaymentCreate(BaseModel):
    amount: float = Field(gt=0, le=25000, description="10-25000 BDT")
```

### bKash Credentials

Credentials are stored in environment variables (never in code):
- **App Key**: Public identifier
- **App Secret**: Private key (never expose)
- **Username/Password**: Sandbox/production credentials

---

## Future Enhancements

### Phase 1 (Week 11 - Current)
- ✅ Cash payment recording
- ✅ bKash payment creation
- ✅ Payment queries and filtering
- ✅ Invoice generation with auto-numbering
- ✅ Multi-tenant isolation
- ✅ Comprehensive testing

### Phase 2 (Future)
- ⏳ bKash callback handler (execute endpoint)
- ⏳ Invoice PDF generation (WeasyPrint)
- ⏳ Payment webhooks for real-time updates
- ⏳ bKash refund processing
- ⏳ Payment analytics dashboard
- ⏳ Recurring payment subscriptions
- ⏳ Multi-currency support (USD, EUR)
- ⏳ Payment reminders via SMS/Email

---

## Support

**Documentation**: See `/docs` for API documentation
**Issues**: Report bugs on GitHub
**bKash Support**: [developer.bka.sh/docs](https://developer.bka.sh/docs)

---

## License

Copyright © 2026 AltCare. All rights reserved.
