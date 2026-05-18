# Payments Frontend Implementation Plan

**Task:** Payments & Billing Frontend  
**Estimated Effort:** 5-7 hours  
**Priority:** HIGH 🔴  
**Status:** IN PROGRESS  
**Started:** 2026-05-19

---

## 📋 Overview

Build complete payments and invoicing frontend to integrate with existing backend (12 endpoints ready).

**Backend Status:** ✅ 100% Complete
- 12 endpoints (payments, invoices, bKash)
- PaymentService implemented
- Multi-tenant isolation ready
- bKash integration functional

**Frontend Goal:** Full payment management UI

---

## 🎯 Deliverables

### 1. Pages (4 pages)
- ✅ `/payments` - Payment dashboard
- ✅ `/payments/transactions` - Transaction history
- ✅ `/payments/invoices` - Invoice management
- ✅ `/payments/invoices/new` - Create invoice

### 2. Components (8-10 components)
- ✅ PaymentSummaryCards
- ✅ RecentTransactionsList
- ✅ PaymentMethodBadge
- ✅ TransactionFilters
- ✅ InvoiceForm
- ✅ InvoiceList
- ✅ PaymentMethodSelector
- ✅ QuickPaymentModal

### 3. Infrastructure
- ✅ TypeScript types (payment.ts)
- ✅ API client (payments.ts)
- ✅ React Query hooks (usePayments.ts)

---

## 📂 File Structure

```
frontend/src/
├── app/(dashboard)/
│   └── payments/
│       ├── page.tsx                    # Dashboard
│       ├── transactions/
│       │   └── page.tsx                # Transaction history
│       ├── invoices/
│       │   ├── page.tsx                # Invoice list
│       │   ├── new/
│       │   │   └── page.tsx            # Create invoice
│       │   └── [id]/
│       │       └── page.tsx            # Invoice detail
│       └── layout.tsx                  # Payments layout (optional)
│
├── components/
│   └── payments/
│       ├── PaymentSummaryCards.tsx
│       ├── RecentTransactionsList.tsx
│       ├── TransactionFilters.tsx
│       ├── PaymentMethodBadge.tsx
│       ├── InvoiceForm.tsx
│       ├── InvoiceList.tsx
│       ├── QuickPaymentModal.tsx
│       └── PaymentMethodSelector.tsx
│
├── lib/
│   ├── api/
│   │   └── payments.ts                 # API client
│   └── hooks/
│       └── usePayments.ts              # React Query hooks
│
└── types/
    └── payment.ts                      # TypeScript types
```

---

## 🔌 Backend APIs (12 endpoints)

### Payments (5 endpoints)
```
POST   /api/v1/payments                 # Create cash payment
GET    /api/v1/payments                 # List payments (filters, pagination)
GET    /api/v1/payments/summary         # Summary stats
GET    /api/v1/payments/{id}            # Get payment detail
```

### bKash (3 endpoints)
```
POST   /api/v1/payments/bkash/create    # Create bKash payment
POST   /api/v1/payments/bkash/execute   # Execute bKash payment
POST   /api/v1/payments/bkash/query     # Query bKash payment status
```

### Invoices (4 endpoints)
```
POST   /api/v1/payments/invoices        # Create invoice
GET    /api/v1/payments/invoices        # List invoices
GET    /api/v1/payments/invoices/{id}   # Get invoice
PATCH  /api/v1/payments/invoices/{id}   # Update invoice status
POST   /api/v1/payments/invoices/{id}/generate-pdf  # Generate PDF
```

---

## 📊 Data Models

### Payment
```typescript
interface Payment {
  id: string;
  tenant_id: string;
  patient_id: string;
  visit_id?: string;
  amount: number;
  currency: string;
  payment_method: 'cash' | 'bkash' | 'nagad' | 'rocket' | 'card';
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  payment_date: string;
  description?: string;
  transaction_id?: string;
  received_by: string;
  created_at: string;
  updated_at: string;
}

interface PaymentSummary {
  total_payments: number;
  total_amount: number;
  paid_amount: number;
  pending_amount: number;
  cash_amount: number;
  bkash_amount: number;
  period_start?: string;
  period_end?: string;
}
```

### Invoice
```typescript
interface Invoice {
  id: string;
  tenant_id: string;
  patient_id: string;
  invoice_number: string;
  amount: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date?: string;
  items: InvoiceItem[];
  notes?: string;
  pdf_url?: string;
  created_at: string;
  updated_at: string;
}

interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}
```

---

## 🎨 UI Features

### Payment Dashboard (`/payments`)
```
┌─────────────────────────────────────────────────┐
│ Summary Cards (4 cards)                         │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│ │Total │ │ Paid │ │Pndng│ │Today │           │
│ └──────┘ └──────┘ └──────┘ └──────┘           │
├─────────────────────────────────────────────────┤
│ Quick Actions                                    │
│ [+ Record Payment] [+ Create Invoice]           │
├─────────────────────────────────────────────────┤
│ Recent Transactions (10 most recent)            │
│ ┌─────────────────────────────────────────────┐│
│ │ Date | Patient | Amount | Method | Status  ││
│ │─────────────────────────────────────────────││
│ │ ...                                         ││
│ └─────────────────────────────────────────────┘│
│ [View All Transactions →]                       │
├─────────────────────────────────────────────────┤
│ Payment Method Breakdown (Pie/Bar Chart)        │
└─────────────────────────────────────────────────┘
```

### Transaction History (`/payments/transactions`)
```
┌─────────────────────────────────────────────────┐
│ Filters                                          │
│ [Date Range] [Method] [Status] [Patient] [Search│
├─────────────────────────────────────────────────┤
│ Transaction List (Table)                         │
│ ┌─────────────────────────────────────────────┐│
│ │ Date | Patient | Amount | Method | Status  ││
│ │─────────────────────────────────────────────││
│ │ 2026-05-19 | John | 1000 | Cash | Paid    ││
│ │ 2026-05-18 | Jane | 1500 | bKash | Paid   ││
│ │ ...                                         ││
│ └─────────────────────────────────────────────┘│
│ Pagination: [< 1 2 3 ... 10 >]                 │
├─────────────────────────────────────────────────┤
│ Export: [CSV] [PDF]                             │
└─────────────────────────────────────────────────┘
```

### Invoice Management (`/payments/invoices`)
```
┌─────────────────────────────────────────────────┐
│ [+ Create Invoice]          [Search] [Filters]  │
├─────────────────────────────────────────────────┤
│ Invoice List (Cards or Table)                   │
│ ┌─────────────────────────────────────────────┐│
│ │ INV-202605-0001 | Patient | 2000 | Paid    ││
│ │ INV-202605-0002 | Patient | 1500 | Sent    ││
│ │ INV-202605-0003 | Patient | 3000 | Draft   ││
│ └─────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│ Status Tabs: [All] [Draft] [Sent] [Paid]       │
└─────────────────────────────────────────────────┘
```

### Create Invoice (`/payments/invoices/new`)
```
┌─────────────────────────────────────────────────┐
│ Create Invoice                                   │
├─────────────────────────────────────────────────┤
│ Patient: [Select Patient ▼]                     │
│ Issue Date: [2026-05-19]                         │
│ Due Date: [Optional]                             │
├─────────────────────────────────────────────────┤
│ Items:                                           │
│ ┌─────────────────────────────────────────────┐│
│ │ Description | Qty | Price | Total          ││
│ │─────────────────────────────────────────────││
│ │ Consultation | 1 | 1000 | 1000            ││
│ │ [+ Add Item]                                ││
│ └─────────────────────────────────────────────┘│
│ Subtotal: 1000                                  │
│ Tax: 0                                          │
│ Total: 1000                                     │
├─────────────────────────────────────────────────┤
│ Notes: [Optional notes]                         │
├─────────────────────────────────────────────────┤
│ [Save as Draft] [Save & Send]                   │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Steps

### Phase 1: Foundation (1-2 hours)
1. ✅ Create TypeScript types (`types/payment.ts`)
2. ✅ Create API client (`lib/api/payments.ts`)
3. ✅ Create React Query hooks (`lib/hooks/usePayments.ts`)
4. ✅ Test API integration

### Phase 2: Dashboard (1-2 hours)
5. ✅ Create payment summary cards component
6. ✅ Create recent transactions list component
7. ✅ Build payment dashboard page
8. ✅ Add quick action buttons

### Phase 3: Transactions (1 hour)
9. ✅ Create transaction filters component
10. ✅ Create transaction list with pagination
11. ✅ Build transactions page
12. ✅ Add export functionality (CSV)

### Phase 4: Invoices (2-3 hours)
13. ✅ Create invoice form component
14. ✅ Create invoice list component
15. ✅ Build invoice pages (list, new, detail)
16. ✅ Add PDF generation

### Phase 5: Polish (30min - 1 hour)
17. ✅ Add loading states
18. ✅ Add error handling
19. ✅ Add success notifications
20. ✅ Test all flows
21. ✅ Update navigation menu

---

## 🎨 Component Specs

### PaymentSummaryCards
```tsx
Props: { summary: PaymentSummary }
Display:
  - Total Payments (count + amount)
  - Paid Amount (with percentage)
  - Pending Amount (with warning if > 0)
  - Today's Revenue
Layout: 4-column grid (responsive: 2x2 on mobile)
```

### RecentTransactionsList
```tsx
Props: { payments: Payment[], limit?: number }
Display:
  - Date, patient name, amount, method badge, status badge
  - Click to view details
  - "View All" link to transactions page
Sorting: Most recent first
Limit: 10 items default
```

### TransactionFilters
```tsx
Props: { onFilter: (filters) => void }
Filters:
  - Date range picker (from/to)
  - Payment method select
  - Status select
  - Patient search/autocomplete
  - Search by transaction ID
Actions: Apply, Clear
```

### PaymentMethodBadge
```tsx
Props: { method: PaymentMethod }
Display:
  - cash: gray badge with "Cash" icon
  - bkash: pink badge with "bKash" logo
  - nagad: orange badge with "Nagad" logo
  - card: blue badge with "Card" icon
```

### InvoiceForm
```tsx
Props: { invoice?: Invoice, onSubmit: (data) => void }
Fields:
  - Patient selector (autocomplete)
  - Issue date (date picker, default today)
  - Due date (date picker, optional)
  - Items array (dynamic add/remove)
    - Description (text)
    - Quantity (number)
    - Unit price (number)
    - Total (calculated)
  - Notes (textarea)
Calculations:
  - Subtotal (auto-calculated)
  - Total (auto-calculated)
Validation:
  - Patient required
  - At least 1 item required
  - Positive numbers only
Actions:
  - Save as Draft
  - Save & Send (marks as "sent")
```

---

## 🔄 User Flows

### Record Cash Payment
1. User clicks "Record Payment" button
2. Modal opens with quick payment form
3. Select patient (autocomplete)
4. Enter amount
5. Add description (optional)
6. Click "Record Payment"
7. Success notification → Payment added to list

### Create Invoice
1. User navigates to /payments/invoices/new
2. Select patient
3. Add invoice items (description, qty, price)
4. Add notes (optional)
5. Choose: Save as Draft OR Save & Send
6. Success → Redirect to invoice list

### View Transaction History
1. User navigates to /payments/transactions
2. Apply filters (optional)
3. View paginated list
4. Click transaction → View details modal
5. Export to CSV (optional)

### bKash Payment (Future Enhancement)
1. Create invoice
2. Select "Pay with bKash"
3. Redirect to bKash
4. User completes payment
5. Return to app → Payment marked as paid

---

## ✅ Acceptance Criteria

### Must Have
- [ ] View payment dashboard with summary stats
- [ ] Record cash payments
- [ ] View transaction history with filters
- [ ] Create and manage invoices
- [ ] View invoice details
- [ ] Update invoice status
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states for all async operations
- [ ] Error handling with user-friendly messages
- [ ] Success notifications

### Nice to Have
- [ ] Export transactions to CSV
- [ ] Payment method breakdown chart
- [ ] Invoice PDF preview
- [ ] bKash payment integration (UI)
- [ ] Print invoice
- [ ] Receipt generation
- [ ] Advanced filters (date shortcuts)
- [ ] Quick stats comparison (this month vs last month)

---

## 🧪 Testing Checklist

### Manual Testing
- [ ] Create cash payment
- [ ] View payment summary
- [ ] Filter transactions by date
- [ ] Filter transactions by method
- [ ] Filter transactions by status
- [ ] Create invoice with multiple items
- [ ] Save invoice as draft
- [ ] Update invoice status
- [ ] View invoice details
- [ ] Test pagination
- [ ] Test responsive layout (mobile)
- [ ] Test error states (API errors)
- [ ] Test loading states

### Integration Testing (Playwright - Optional)
- [ ] Payment creation flow
- [ ] Invoice creation flow
- [ ] Transaction filtering
- [ ] Pagination

---

## 📝 Notes

### Backend APIs Available
- ✅ All payment CRUD operations
- ✅ Payment summary/statistics
- ✅ Invoice management
- ✅ bKash integration (create, execute, query)
- ✅ Pagination and filtering
- ✅ Multi-tenant isolation

### Design Considerations
- Match existing shadcn/ui components
- Follow patterns from patients/prescriptions modules
- Use existing components (Button, Card, Table, Badge, Form)
- Consistent color scheme for payment methods
- Mobile-first responsive design

### Security
- All APIs require authentication (JWT)
- Multi-tenant isolation enforced automatically
- No sensitive data in URLs
- Encrypted bKash credentials (backend)

---

## 🚀 Next Steps After Completion

1. Update navigation menu (add Payments link)
2. Add payment quick actions to dashboard
3. Link payments to patient profile
4. Link payments to appointments/visits
5. Implement notification system (payment reminders)
6. Add bKash payment UI flow
7. Generate PDF invoices (frontend or backend)
8. Add payment analytics/reports

---

**Implementation Start:** 2026-05-19  
**Target Completion:** 2026-05-19 (same day)  
**Estimated Time:** 5-7 hours
