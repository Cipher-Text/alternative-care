# Phase 1 Development Kickoff
## AltCare UX Improvements - Week 1-4 Implementation

**Status**: 🚀 Ready to Start  
**Timeline**: 4 weeks  
**Team**: Frontend (React/Next.js) + Backend (FastAPI)  
**Expected Impact**: +20% activation, +12% engagement, +10% conversion

---

## 📋 Sprint Overview

### Week 1-2: Core Components
- [ ] Onboarding checklist system
- [ ] Quick actions floating button
- [ ] Enhanced empty states (5 templates)
- [ ] Command palette (Cmd+K)

### Week 3-4: Smart Features
- [ ] Contextual upgrade prompts
- [ ] Help widget with tooltips
- [ ] Allergy warning modal
- [ ] Smart KPI insights

---

## 🎯 Quick Win #1: Onboarding Checklist Widget

### Specification
**Component**: `<OnboardingChecklist />`  
**Location**: Dashboard page (top, dismissible)  
**Priority**: 🔴 Critical - Drives 40% activation increase

### User Story
```
As a new doctor,
I want a guided setup checklist,
So I can quickly configure my practice and start using AltCare.
```

### Design Specs
```
┌──────────────────────────────────────────────────┐
│ 🎯 Complete your setup (4/8 completed)          │
│ [███████░░░░░░░] 50%                            │
│                                                  │
│ ✓ Profile created                                │
│ ✓ Degrees verified                               │
│ ✓ Clinic location added                          │
│ ✓ First patient added                            │
│ ○ Create first prescription                      │
│ ○ Set up payment tracking                        │
│ ○ Upload prescription template                   │
│ ○ Explore AI assistant (Pro)                     │
│                                                  │
│ [Continue Setup →]        [Dismiss]              │
└──────────────────────────────────────────────────┘

Colors:
- Background: White with soft gradient
- Border: 1px solid var(--g4) / #5DCAA5
- Progress bar: Gradient from --g5 to --g6
- Check icon: --g6 / #0F6E56
- Incomplete: --color-text-tertiary
```

### React Component (Next.js 14 + TypeScript)

```typescript
// components/dashboard/OnboardingChecklist.tsx
'use client';

import { useState, useEffect } from 'react';
import { X, Check, Circle } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ChecklistItem {
  id: string;
  label: string;
  completed: boolean;
  action?: string;
  isPro?: boolean;
}

interface OnboardingChecklistProps {
  userId: string;
}

export function OnboardingChecklist({ userId }: OnboardingChecklistProps) {
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [dismissed, setDismissed] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetchChecklistProgress();
  }, [userId]);

  const fetchChecklistProgress = async () => {
    const res = await fetch(`/api/onboarding/progress/${userId}`);
    const data = await res.json();
    setItems(data.items);
    setDismissed(data.dismissed);
  };

  const completedCount = items.filter(i => i.completed).length;
  const totalCount = items.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  const handleDismiss = async () => {
    await fetch(`/api/onboarding/dismiss/${userId}`, { method: 'POST' });
    setDismissed(true);
  };

  const handleContinue = () => {
    const nextIncomplete = items.find(i => !i.completed);
    if (nextIncomplete?.action) {
      router.push(nextIncomplete.action);
    }
  };

  if (dismissed || completedCount === totalCount) return null;

  return (
    <div className="bg-white rounded-xl border border-green-200 p-5 mb-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-900">
            🎯 Complete your setup ({completedCount}/{totalCount} completed)
          </h3>
        </div>
        <button
          onClick={handleDismiss}
          className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100"
          aria-label="Dismiss checklist"
        >
          <X size={16} />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">{progressPercent}% complete</p>
      </div>

      {/* Checklist Items */}
      <div className="space-y-2 mb-4">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex items-center gap-3 py-1.5 px-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            {item.completed ? (
              <Check size={16} className="text-green-600 flex-shrink-0" />
            ) : (
              <Circle size={16} className="text-gray-300 flex-shrink-0" />
            )}
            <span className={`text-sm flex-1 ${
              item.completed ? 'text-gray-500 line-through' : 'text-gray-700'
            }`}>
              {item.label}
              {item.isPro && (
                <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                  Pro
                </span>
              )}
            </span>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleContinue}
          className="btn-primary text-sm px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
        >
          Continue Setup →
        </button>
        <button
          onClick={handleDismiss}
          className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
```

### API Endpoints (FastAPI)

```python
# backend/app/api/routes/onboarding.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.onboarding import OnboardingProgress

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

@router.get("/progress/{user_id}", response_model=OnboardingProgress)
async def get_onboarding_progress(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's onboarding checklist progress"""
    
    # Check completion status for each step
    has_profile = await check_profile_complete(db, user_id)
    has_degrees = await check_degrees_verified(db, user_id)
    has_location = await check_clinic_location(db, user_id)
    has_patient = await check_first_patient(db, user_id)
    has_prescription = await check_first_prescription(db, user_id)
    has_payment = await check_payment_setup(db, user_id)
    has_template = await check_prescription_template(db, user_id)
    explored_ai = await check_ai_explored(db, user_id)
    
    # Get dismissed status
    dismissed = await get_checklist_dismissed(db, user_id)
    
    return {
        "items": [
            {"id": "profile", "label": "Profile created", "completed": has_profile, "action": "/settings/profile"},
            {"id": "degrees", "label": "Degrees verified", "completed": has_degrees, "action": "/settings/profile#degrees"},
            {"id": "location", "label": "Clinic location added", "completed": has_location, "action": "/settings/clinic"},
            {"id": "patient", "label": "First patient added", "completed": has_patient, "action": "/patients/new"},
            {"id": "prescription", "label": "Create first prescription", "completed": has_prescription, "action": "/prescriptions/new"},
            {"id": "payment", "label": "Set up payment tracking", "completed": has_payment, "action": "/payments/setup"},
            {"id": "template", "label": "Upload prescription template", "completed": has_template, "action": "/settings/templates"},
            {"id": "ai", "label": "Explore AI assistant", "completed": explored_ai, "action": "/ai", "isPro": True},
        ],
        "dismissed": dismissed
    }

@router.post("/dismiss/{user_id}")
async def dismiss_checklist(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dismiss onboarding checklist"""
    await set_checklist_dismissed(db, user_id, True)
    return {"status": "dismissed"}

# Helper functions
async def check_profile_complete(db: AsyncSession, user_id: str) -> bool:
    # Check if user has name, email, phone, specialization
    result = await db.execute(
        "SELECT COUNT(*) FROM users WHERE id = :user_id AND name IS NOT NULL AND email IS NOT NULL",
        {"user_id": user_id}
    )
    return result.scalar() > 0

async def check_degrees_verified(db: AsyncSession, user_id: str) -> bool:
    # Check if at least one degree is verified
    result = await db.execute(
        "SELECT COUNT(*) FROM doctor_degrees WHERE user_id = :user_id AND verification_status = 'verified'",
        {"user_id": user_id}
    )
    return result.scalar() > 0

# ... implement other check functions
```

### Database Migration (Alembic)

```python
# alembic/versions/xxx_add_onboarding_tracking.py
"""Add onboarding tracking

Revision ID: xxx
Revises: yyy
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'onboarding_progress',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.String, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('checklist_dismissed', sa.Boolean, default=False),
        sa.Column('ai_explored', sa.Boolean, default=False),
        sa.Column('first_patient_at', sa.DateTime, nullable=True),
        sa.Column('first_prescription_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_onboarding_user', 'onboarding_progress', ['user_id'])

def downgrade():
    op.drop_table('onboarding_progress')
```

### Testing Criteria

```typescript
// __tests__/OnboardingChecklist.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OnboardingChecklist } from '@/components/dashboard/OnboardingChecklist';

describe('OnboardingChecklist', () => {
  it('shows progress correctly', async () => {
    render(<OnboardingChecklist userId="test-user" />);
    
    await waitFor(() => {
      expect(screen.getByText(/4\/8 completed/i)).toBeInTheDocument();
      expect(screen.getByText(/50% complete/i)).toBeInTheDocument();
    });
  });

  it('dismisses when X clicked', async () => {
    render(<OnboardingChecklist userId="test-user" />);
    
    const dismissBtn = screen.getByLabelText('Dismiss checklist');
    fireEvent.click(dismissBtn);
    
    await waitFor(() => {
      expect(screen.queryByText(/Complete your setup/i)).not.toBeInTheDocument();
    });
  });

  it('navigates on Continue Setup', async () => {
    const mockRouter = { push: jest.fn() };
    render(<OnboardingChecklist userId="test-user" />);
    
    const continueBtn = screen.getByText('Continue Setup →');
    fireEvent.click(continueBtn);
    
    expect(mockRouter.push).toHaveBeenCalledWith('/patients/new');
  });

  it('hides when all items completed', () => {
    // Mock all items as completed
    render(<OnboardingChecklist userId="complete-user" />);
    
    expect(screen.queryByText(/Complete your setup/i)).not.toBeInTheDocument();
  });
});
```

### Definition of Done
- [ ] Component renders with live data from API
- [ ] Progress bar animates smoothly
- [ ] Dismiss persists to database
- [ ] Continue button navigates to next incomplete step
- [ ] Hides when 100% complete or dismissed
- [ ] Mobile responsive (stacks on <768px)
- [ ] Unit tests pass (>80% coverage)
- [ ] Accessible (keyboard nav, screen readers)
- [ ] Tested with 5 beta users
- [ ] Analytics tracking implemented

---

## 🎯 Quick Win #2: Quick Actions Floating Button

### Specification
**Component**: `<QuickActionsMenu />`  
**Location**: Global (bottom-right, all pages)  
**Priority**: 🟡 High - Saves 3-5 clicks per task

### Design Specs
```
Bottom-right corner (fixed position):

┌─────────────┐
│     [+]     │ ← Floating circular button (56px)
└─────────────┘
      ↓ Opens radial menu on click:
      
      • 👤 New Patient
      • 💊 New Prescription  
      • 💳 Record Payment
      • 📝 Quick Note
      • 🔍 Search Medicine
      • ⚙️ Settings

Keyboard: Cmd/Ctrl + K opens command palette
Mobile: Bottom-center (48px from bottom)
```

### React Component

```typescript
// components/global/QuickActionsMenu.tsx
'use client';

import { useState, useEffect } from 'react';
import { Plus, X, User, Pill, CreditCard, FileText, Search, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useHotkeys } from 'react-hotkeys-hook';

const actions = [
  { id: 'patient', icon: User, label: 'New Patient', href: '/patients/new', color: 'blue' },
  { id: 'prescription', icon: Pill, label: 'New Prescription', href: '/prescriptions/new', color: 'green' },
  { id: 'payment', icon: CreditCard, label: 'Record Payment', href: '/payments/new', color: 'purple' },
  { id: 'note', icon: FileText, label: 'Quick Note', href: '/notes/new', color: 'amber' },
  { id: 'search', icon: Search, label: 'Search Medicine', href: '/medicines', color: 'teal' },
  { id: 'settings', icon: Settings, label: 'Settings', href: '/settings', color: 'gray' },
];

export function QuickActionsMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  // Keyboard shortcut: Cmd/Ctrl + K
  useHotkeys('mod+k', (e) => {
    e.preventDefault();
    setIsOpen(prev => !prev);
  });

  const handleAction = (href: string) => {
    setIsOpen(false);
    router.push(href);
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-all duration-300 ${
            isOpen
              ? 'bg-red-500 rotate-45'
              : 'bg-green-600 hover:bg-green-700 hover:shadow-xl'
          }`}
          aria-label={isOpen ? 'Close quick actions' : 'Open quick actions'}
        >
          {isOpen ? (
            <X size={24} className="text-white" />
          ) : (
            <Plus size={24} className="text-white" />
          )}
        </button>

        {/* Action Menu */}
        {isOpen && (
          <div className="absolute bottom-20 right-0 flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-4 duration-200">
            {actions.map((action, index) => (
              <div
                key={action.id}
                className="flex items-center gap-3 animate-in slide-in-from-right duration-200"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <span className="text-sm font-medium text-gray-700 bg-white px-3 py-1.5 rounded-lg shadow-md whitespace-nowrap">
                  {action.label}
                </span>
                <button
                  onClick={() => handleAction(action.href)}
                  className={`w-12 h-12 rounded-full shadow-lg flex items-center justify-center bg-${action.color}-500 hover:bg-${action.color}-600 transition-colors`}
                  aria-label={action.label}
                >
                  <action.icon size={20} className="text-white" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keyboard Hint (first 3 sessions) */}
      {!isOpen && <KeyboardHint />}
    </>
  );
}

function KeyboardHint() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const visits = localStorage.getItem('quickActionsVisits') || '0';
    const count = parseInt(visits);
    
    if (count < 3) {
      setShow(true);
      localStorage.setItem('quickActionsVisits', String(count + 1));
      
      setTimeout(() => setShow(false), 5000);
    }
  }, []);

  if (!show) return null;

  return (
    <div className="fixed bottom-24 right-6 bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg animate-bounce">
      Press <kbd className="bg-gray-700 px-1.5 py-0.5 rounded">⌘K</kbd> for quick actions
    </div>
  );
}
```

### Testing Criteria
- [ ] Opens/closes on button click
- [ ] Opens on Cmd+K / Ctrl+K
- [ ] All 6 actions navigate correctly
- [ ] Closes on backdrop click
- [ ] Closes on Escape key
- [ ] Mobile: renders bottom-center
- [ ] Keyboard hint shows first 3 visits
- [ ] Animations smooth (60fps)
- [ ] Accessible (focus trap when open)
- [ ] Analytics: track most-used action

---

## 🎯 Quick Win #3: Command Palette (Cmd+K)

### Specification
**Component**: `<CommandPalette />`  
**Location**: Global overlay  
**Priority**: 🟡 High - 5x faster navigation

### Design Specs
```
Modal overlay (centered):

┌──────────────────────────────────────┐
│ ⌘ Quick search...                    │ ← Search input
├──────────────────────────────────────┤
│ Recent                               │
│ 👤 Fatima Ahmed - View profile       │
│ 💊 Rhus Tox 30C - View details      │
│                                      │
│ Quick Actions                        │
│ ⚡ Add new patient                   │
│ ⚡ Create prescription                │
│                                      │
│ Navigate                             │
│ 📊 Dashboard                         │
│ 👥 Patients                          │
│ 💊 Medicines                         │
└──────────────────────────────────────┘

Features:
- Fuzzy search
- Keyboard navigation (↑↓ Enter)
- Groups: Recent, Actions, Navigate
- Highlights matched text
- Shows keyboard shortcuts
```

### React Component (using cmdk library)

```typescript
// components/global/CommandPalette.tsx
'use client';

import { useEffect, useState } from 'react';
import { Command } from 'cmdk';
import { useRouter } from 'next/navigation';
import { useHotkeys } from 'react-hotkeys-hook';
import {
  Search, User, Pill, FileText, BarChart3, Settings,
  Zap, Calendar, CreditCard
} from 'lucide-react';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [recentItems, setRecentItems] = useState([]);
  const router = useRouter();

  // Toggle with Cmd+K
  useHotkeys('mod+k', (e) => {
    e.preventDefault();
    setOpen(o => !o);
  });

  // Close on Escape
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  // Fetch recent items
  useEffect(() => {
    if (open) {
      fetchRecentItems();
    }
  }, [open]);

  const fetchRecentItems = async () => {
    const res = await fetch('/api/user/recent');
    const data = await res.json();
    setRecentItems(data);
  };

  const runCommand = (command: () => void) => {
    setOpen(false);
    command();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm">
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl">
        <Command className="bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          <div className="flex items-center border-b border-gray-200 px-4">
            <Search size={18} className="text-gray-400" />
            <Command.Input
              value={search}
              onValueChange={setSearch}
              placeholder="Type to search..."
              className="w-full py-3 px-3 text-sm outline-none bg-transparent"
            />
            <kbd className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">ESC</kbd>
          </div>

          <Command.List className="max-h-96 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-gray-500">
              No results found.
            </Command.Empty>

            {/* Recent */}
            {recentItems.length > 0 && (
              <Command.Group heading="Recent" className="text-xs text-gray-500 px-2 py-1.5 font-semibold">
                {recentItems.map((item: any) => (
                  <Command.Item
                    key={item.id}
                    onSelect={() => runCommand(() => router.push(item.href))}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
                  >
                    <item.icon size={16} className="text-gray-400" />
                    <span className="text-sm">{item.label}</span>
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            {/* Quick Actions */}
            <Command.Group heading="Quick Actions" className="text-xs text-gray-500 px-2 py-1.5 font-semibold">
              <Command.Item
                onSelect={() => runCommand(() => router.push('/patients/new'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <Zap size={16} className="text-blue-500" />
                <span className="text-sm">Add new patient</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push('/prescriptions/new'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <Zap size={16} className="text-green-500" />
                <span className="text-sm">Create prescription</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push('/payments/new'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <Zap size={16} className="text-purple-500" />
                <span className="text-sm">Record payment</span>
              </Command.Item>
            </Command.Group>

            {/* Navigate */}
            <Command.Group heading="Navigate" className="text-xs text-gray-500 px-2 py-1.5 font-semibold">
              <Command.Item
                onSelect={() => runCommand(() => router.push('/dashboard'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <BarChart3 size={16} className="text-gray-400" />
                <span className="text-sm">Dashboard</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push('/patients'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <User size={16} className="text-gray-400" />
                <span className="text-sm">Patients</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push('/medicines'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <Pill size={16} className="text-gray-400" />
                <span className="text-sm">Medicines</span>
              </Command.Item>
              <Command.Item
                onSelect={() => runCommand(() => router.push('/settings'))}
                className="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer hover:bg-gray-100 data-[selected]:bg-gray-100"
              >
                <Settings size={16} className="text-gray-400" />
                <span className="text-sm">Settings</span>
              </Command.Item>
            </Command.Group>
          </Command.List>

          <div className="border-t border-gray-200 px-4 py-2 text-xs text-gray-500 flex items-center gap-4">
            <div className="flex items-center gap-1">
              <kbd className="bg-gray-100 px-1.5 py-0.5 rounded">↑↓</kbd> Navigate
            </div>
            <div className="flex items-center gap-1">
              <kbd className="bg-gray-100 px-1.5 py-0.5 rounded">Enter</kbd> Select
            </div>
            <div className="flex items-center gap-1">
              <kbd className="bg-gray-100 px-1.5 py-0.5 rounded">ESC</kbd> Close
            </div>
          </div>
        </Command>
      </div>
    </div>
  );
}
```

### Package Installation
```bash
npm install cmdk
npm install react-hotkeys-hook
npm install lucide-react
```

### Testing Criteria
- [ ] Opens on Cmd+K (Mac) / Ctrl+K (Windows)
- [ ] Closes on Escape
- [ ] Closes on backdrop click
- [ ] Arrow keys navigate items
- [ ] Enter selects highlighted item
- [ ] Fuzzy search works (e.g., "pat" finds "Patients")
- [ ] Recent items load from API
- [ ] Mobile: full-screen modal
- [ ] Accessible (focus management)
- [ ] Analytics: track search terms

---

## 🎯 Quick Win #4: Enhanced Empty States

### Specification
**Components**: 5 reusable empty state templates  
**Priority**: 🟢 Medium - Guides users to action

### Templates

#### 1. No Patients Yet
```typescript
// components/empty-states/NoPatients.tsx
export function NoPatients() {
  return (
    <div className="text-center py-12 px-4">
      <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
        <User size={32} className="text-blue-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        No patients yet
      </h3>
      <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
        Add your first patient to start managing records digitally
      </p>
      <div className="flex gap-3 justify-center">
        <button className="btn-primary">
          + Add Patient
        </button>
        <button className="btn-ghost">
          Import from CSV
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-4">
        💡 Tip: Most doctors add 10-20 existing patients in their first session
      </p>
    </div>
  );
}
```

#### 2. No Prescriptions Yet
```typescript
// components/empty-states/NoPrescriptions.tsx
export function NoPrescriptions() {
  return (
    <div className="text-center py-12 px-4">
      <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
        <FileText size={32} className="text-green-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        No prescriptions created
      </h3>
      <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
        Create your first prescription with our easy-to-use builder
      </p>
      <button className="btn-primary">
        + Create Prescription
      </button>
      <p className="text-xs text-gray-500 mt-4">
        💡 Your prescription templates will appear here
      </p>
    </div>
  );
}
```

#### 3. No Payments Recorded
```typescript
// components/empty-states/NoPayments.tsx
export function NoPayments() {
  return (
    <div className="text-center py-12 px-4">
      <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
        <CreditCard size={32} className="text-purple-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        No payments recorded
      </h3>
      <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
        Start tracking revenue by recording your first payment
      </p>
      <button className="btn-primary">
        + Record Payment
      </button>
      <p className="text-xs text-gray-500 mt-4">
        Connect bKash, Nagad, or Stripe for automated tracking
      </p>
    </div>
  );
}
```

#### 4. Search No Results
```typescript
// components/empty-states/NoSearchResults.tsx
export function NoSearchResults({ query }: { query: string }) {
  return (
    <div className="text-center py-12 px-4">
      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
        <Search size={32} className="text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        No results for "{query}"
      </h3>
      <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
        Try adjusting your search or filters
      </p>
      <div className="flex gap-3 justify-center">
        <button className="btn-ghost">
          Clear filters
        </button>
        <button className="btn-ghost">
          Search all
        </button>
      </div>
    </div>
  );
}
```

#### 5. Feature Locked (Free Plan)
```typescript
// components/empty-states/FeatureLocked.tsx
export function FeatureLocked({ featureName }: { featureName: string }) {
  return (
    <div className="text-center py-12 px-4 border-2 border-dashed border-purple-300 rounded-xl bg-purple-50">
      <div className="w-16 h-16 mx-auto mb-4 bg-purple-200 rounded-full flex items-center justify-center">
        <Lock size={32} className="text-purple-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {featureName} (Pro Feature)
      </h3>
      <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
        Upgrade to Pro to unlock AI-powered insights and clinical support
      </p>
      <div className="flex gap-3 justify-center">
        <button className="btn-primary bg-purple-600 hover:bg-purple-700">
          Start Free Trial
        </button>
        <button className="btn-ghost">
          Learn More
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-4">
        ✨ 14-day free trial • No credit card required
      </p>
    </div>
  );
}
```

### Usage Example
```typescript
// pages/patients/index.tsx
import { NoPatients } from '@/components/empty-states/NoPatients';

export default function PatientsPage() {
  const { data: patients, isLoading } = usePatients();

  if (isLoading) return <LoadingSkeleton />;
  
  if (patients.length === 0) {
    return <NoPatients />;
  }

  return <PatientsTable patients={patients} />;
}
```

---

## 🎯 Quick Win #5: Contextual Upgrade Prompts

### Specification
**Component**: `<UpgradePrompt />`  
**Location**: Contextual (usage-triggered)  
**Priority**: 🔴 Critical - Drives 22% conversion

### Scenarios

#### Scenario 1: Approaching Patient Limit (Free Plan)
```typescript
// components/upgrade/PatientLimitWarning.tsx
export function PatientLimitWarning({ used, limit }: { used: number; limit: number }) {
  const percentUsed = Math.round((used / limit) * 100);
  
  if (percentUsed < 85) return null; // Only show at 85%+

  return (
    <div className={`rounded-xl p-4 mb-6 ${
      percentUsed >= 95 ? 'bg-red-50 border-2 border-red-200' : 'bg-amber-50 border-2 border-amber-200'
    }`}>
      <div className="flex items-start gap-3">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
          percentUsed >= 95 ? 'bg-red-100' : 'bg-amber-100'
        }`}>
          <AlertTriangle size={20} className={percentUsed >= 95 ? 'text-red-600' : 'text-amber-600'} />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-sm mb-1">
            {percentUsed >= 95 ? 'Almost at patient limit!' : 'Approaching patient limit'}
          </h4>
          <p className="text-sm text-gray-700 mb-3">
            {used}/{limit} patients ({percentUsed}% used)
            {percentUsed >= 95 && ' — Add patients soon before hitting limit'}
          </p>
          <div className="flex gap-3">
            <button className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700">
              Upgrade to Plus → 500 patients for ৳799/mo
            </button>
            {percentUsed < 95 && (
              <button className="text-sm text-gray-600 hover:text-gray-800">
                Remind me at {limit - 1}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### Scenario 2: AI Assistant Click (Free/Plus Plan)
```typescript
// components/upgrade/AIFeatureTeaser.tsx
export function AIFeatureTeaser() {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md p-6 shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles size={32} className="text-purple-600" />
          </div>
          <h3 className="text-xl font-semibold mb-2">
            AI Assistant (Pro Feature)
          </h3>
          <p className="text-sm text-gray-600">
            Get instant answers from classical texts + AI-powered remedy suggestions
          </p>
        </div>

        <div className="bg-gray-50 rounded-xl p-4 mb-6">
          <div className="text-sm text-gray-700 mb-3">
            <strong>Example questions:</strong>
          </div>
          <ul className="text-sm text-gray-600 space-y-2">
            <li>• "What remedies for chronic arthritis in elderly?"</li>
            <li>• "Summarize Organon Chapter 3"</li>
            <li>• "Compare Rhus Tox vs Bryonia for joint pain"</li>
          </ul>
        </div>

        <div className="space-y-3">
          <button className="w-full bg-purple-600 text-white py-3 rounded-lg font-medium hover:bg-purple-700">
            Start 14-Day Free Trial
          </button>
          <button className="w-full text-gray-600 py-2 text-sm hover:text-gray-800">
            Learn more about Pro
          </button>
        </div>

        <p className="text-xs text-gray-500 text-center mt-4">
          ✨ No credit card required • Cancel anytime
        </p>
      </div>
    </div>
  );
}
```

#### Scenario 3: Export PDF (Free Plan)
```typescript
// components/upgrade/PDFExportLocked.tsx
export function PDFExportLocked() {
  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <FileDown size={20} className="text-blue-600" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-sm mb-1">
            PDF Export (Plus Feature)
          </h4>
          <p className="text-sm text-gray-700 mb-3">
            Upgrade to Plus to export professional PDF prescriptions
          </p>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
            Upgrade to Plus — ৳799/mo
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Backend: Usage Tracking API
```python
# backend/app/api/routes/usage.py
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, get_db

router = APIRouter(prefix="/api/usage", tags=["usage"])

@router.get("/limits")
async def get_user_limits(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's current usage vs plan limits"""
    
    plan = await get_user_plan(db, current_user.id)
    
    # Count usage
    patient_count = await count_patients(db, current_user.id)
    prescription_count_month = await count_prescriptions_month(db, current_user.id)
    ai_queries_month = await count_ai_queries_month(db, current_user.id)
    
    # Plan limits
    limits = {
        "free": {"patients": 30, "prescriptions": 10, "ai_queries": 0},
        "plus": {"patients": 500, "prescriptions": -1, "ai_queries": 0},  # -1 = unlimited
        "pro": {"patients": -1, "prescriptions": -1, "ai_queries": 200}
    }
    
    plan_limits = limits[plan.name.lower()]
    
    return {
        "plan": plan.name,
        "usage": {
            "patients": patient_count,
            "prescriptions_this_month": prescription_count_month,
            "ai_queries_this_month": ai_queries_month
        },
        "limits": plan_limits,
        "warnings": {
            "patient_limit_approaching": patient_count >= plan_limits["patients"] * 0.85 if plan_limits["patients"] > 0 else False,
            "prescription_limit_reached": plan_limits["prescriptions"] > 0 and prescription_count_month >= plan_limits["prescriptions"],
            "ai_limit_approaching": plan_limits["ai_queries"] > 0 and ai_queries_month >= plan_limits["ai_queries"] * 0.8
        }
    }
```

---

## 📦 Package Dependencies

### Frontend (Next.js 14 + React)
```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "typescript": "5.3.3",
    "tailwindcss": "3.4.1",
    "cmdk": "^0.2.1",
    "react-hotkeys-hook": "^4.4.1",
    "lucide-react": "^0.312.0",
    "@tanstack/react-query": "^5.17.0",
    "framer-motion": "^11.0.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0",
    "jest": "^29.7.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

### Backend (FastAPI + Python)
```python
# requirements.txt (additions for Phase 1)
pydantic-settings==2.2.1  # Already have
fastapi==0.110.0  # Already have
sqlalchemy[asyncio]==2.0.28  # Already have
alembic==1.13.0  # Already have

# New for analytics
mixpanel==4.10.1
posthog==3.1.0
```

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Frontend
npm test -- --coverage --watchAll=false

# Target: >80% coverage for new components
```

### Integration Tests
```typescript
// __tests__/integration/onboarding-flow.test.tsx
describe('Onboarding Flow', () => {
  it('completes full onboarding journey', async () => {
    // 1. Login as new user
    // 2. See onboarding checklist (0/8)
    // 3. Click "Continue Setup"
    // 4. Complete each step
    // 5. Checklist shows 8/8
    // 6. Checklist disappears
  });
});
```

### E2E Tests (Playwright)
```typescript
// e2e/quick-actions.spec.ts
import { test, expect } from '@playwright/test';

test('quick actions menu works', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Click floating button
  await page.click('[aria-label="Open quick actions"]');
  
  // Menu appears
  await expect(page.locator('text=New Patient')).toBeVisible();
  
  // Click action
  await page.click('text=New Patient');
  
  // Navigates correctly
  await expect(page).toHaveURL('/patients/new');
});
```

---

## 📊 Analytics Events

### Track These Events (Mixpanel/PostHog)
```typescript
// utils/analytics.ts
export const trackEvent = (eventName: string, properties?: object) => {
  // Mixpanel
  mixpanel.track(eventName, properties);
  
  // PostHog
  posthog.capture(eventName, properties);
};

// Events to track:
trackEvent('onboarding_checklist_viewed', { step_count: 8, completed_count: 4 });
trackEvent('onboarding_step_completed', { step: 'first_patient' });
trackEvent('onboarding_dismissed', { completed_percent: 50 });
trackEvent('quick_actions_opened', { trigger: 'button' }); // or 'keyboard'
trackEvent('quick_action_used', { action: 'new_patient' });
trackEvent('command_palette_opened');
trackEvent('command_palette_search', { query: 'fatima' });
trackEvent('upgrade_prompt_shown', { trigger: 'patient_limit', plan: 'free' });
trackEvent('upgrade_prompt_clicked', { trigger: 'patient_limit', plan: 'free' });
trackEvent('empty_state_cta_clicked', { state: 'no_patients', action: 'add_patient' });
```

---

## ✅ Sprint Checklist

### Week 1: Setup & Foundation
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Set up Tailwind CSS + design tokens
- [ ] Install dependencies (cmdk, framer-motion, etc.)
- [ ] Create database migration for onboarding_progress
- [ ] Set up API routes structure
- [ ] Configure analytics (Mixpanel/PostHog)
- [ ] Set up testing (Jest, Playwright)

### Week 2: Core Components
- [ ] Build OnboardingChecklist component
- [ ] Build QuickActionsMenu component
- [ ] Build CommandPalette component
- [ ] Create 5 empty state templates
- [ ] Build UpgradePrompt variants (3 scenarios)
- [ ] Write unit tests (>80% coverage)
- [ ] Write integration tests

### Week 3: API Integration
- [ ] Implement `/api/onboarding/progress` endpoint
- [ ] Implement `/api/usage/limits` endpoint
- [ ] Implement `/api/user/recent` endpoint
- [ ] Add analytics tracking to all components
- [ ] Test with live data
- [ ] Performance optimization

### Week 4: Polish & Launch
- [ ] E2E tests (Playwright)
- [ ] Mobile responsive testing
- [ ] Accessibility audit (WCAG AA)
- [ ] Beta testing with 10 doctors
- [ ] Fix bugs from beta feedback
- [ ] Deploy to staging
- [ ] Deploy to production
- [ ] Monitor metrics (activation rate)

---

## 🎯 Success Metrics (Week 4 Goals)

**Baseline (Before Phase 1):**
- Activation rate: 35%
- Weekly active users: 28%
- Free → Plus conversion: 5%
- Support tickets: 0.4/user/month

**Target (After Phase 1):**
- ✅ Activation rate: >50% (+43%)
- ✅ Weekly active users: >40% (+43%)
- ✅ Free → Plus conversion: >8% (+60%)
- ✅ Support tickets: <0.25/user/month (-37%)

**How to Measure:**
```sql
-- Activation rate
SELECT 
  COUNT(DISTINCT user_id) FILTER (WHERE steps_completed >= 5) * 100.0 / 
  COUNT(DISTINCT user_id) as activation_rate
FROM onboarding_progress
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Weekly active users
SELECT 
  COUNT(DISTINCT user_id) as weekly_active
FROM user_sessions
WHERE last_active >= NOW() - INTERVAL '7 days';
```

---

## 📞 Support & Resources

### Team Contacts
- **Product Manager**: [Name] - Decisions, priorities
- **Lead Frontend**: [Name] - React/Next.js questions
- **Lead Backend**: [Name] - FastAPI/database questions
- **Designer**: [Name] - UI/UX reviews

### Documentation
- **Design System**: Figma link (TBD)
- **API Docs**: Swagger at `/api/docs`
- **Component Storybook**: `/storybook`
- **Project Board**: GitHub Projects / Jira

### Daily Standup
- **Time**: 10:00 AM Bangladesh Time (GMT+6)
- **Format**: Async (Slack) or sync (Zoom)
- **Updates**: What I did, what I'm doing, blockers

---

## 🚀 Let's Ship!

**Remember:**
- Ship 80% solution fast
- Get feedback from real users
- Iterate weekly
- Measure everything
- Perfect is the enemy of good

**Next Steps:**
1. Review this document with team (1 hour)
2. Set up development environment
3. Create tasks in project board
4. Start Week 1 sprint
5. Daily standups + weekly demos

Good luck! 🎉

---

*Document version: 1.0*  
*Created: 2026-04-21*  
*Status: Ready for development*  
*Estimated completion: May 19, 2026 (4 weeks)*
