export type SubscriptionPlan = 'free' | 'plus' | 'pro' | 'enterprise'
export type UserRole = 'admin' | 'operator' | 'doctor' | 'receptionist'

// ============================================================================
// Dashboard
// ============================================================================

export interface AdminDashboard {
  total_tenants: number
  active_tenants: number
  pending_approvals: number
  total_doctors: number
  total_users: number
  plans: {
    free: number
    plus: number
    pro: number
    enterprise: number
  }
}

// ============================================================================
// Tenant
// ============================================================================

export interface AdminTenantItem {
  id: string
  name: string
  email: string
  clinic_name: string | null
  specializations: string[]
  plan: string
  plan_expires_at?: string | null
  is_verified: boolean
  is_approved: boolean
  is_active: boolean
  approved_at: string | null
  created_at: string
}

export interface AdminTenantDoctorItem {
  id: string
  email: string
  full_name: string
  phone: string | null
  role: string
  is_active: boolean
  is_email_verified: boolean
  last_login_at: string | null
  created_at: string
}

export interface AdminTenantListItem {
  tenant: AdminTenantItem
  primary_doctor: AdminTenantDoctorItem | null
  doctor_count: number
  created_at: string
}

export interface AdminTenantDetail {
  tenant: AdminTenantItem
  doctors: AdminTenantDoctorItem[]
  created_at: string
  updated_at: string | null
  approved_at: string | null
  approved_by: string | null
}

export interface AdminUpdateTenantRequest {
  plan?: SubscriptionPlan
  is_active?: boolean
  is_approved?: boolean
}

// ============================================================================
// Provision
// ============================================================================

export interface AdminProvisionRequest {
  email: string
  password: string
  full_name: string
  phone?: string | null
  language: 'en' | 'bn'
  tenant_name?: string | null
  clinic_name?: string | null
  clinic_address?: string | null
  division_id?: number | null
  district_id?: number | null
  upazila_id?: number | null
  specializations: string[]
  license_number?: string | null
  plan: SubscriptionPlan
  auto_approve: boolean
}

export interface AdminProvisionResponse {
  message: string
  user_id: string
  tenant_id: string
  email: string
  requires_approval: boolean
}

export interface AdminAddTenantDoctorRequest {
  email: string
  password: string
  full_name: string
  phone?: string | null
  language: 'en' | 'bn'
}

export interface AdminAddTenantDoctorResponse {
  message: string
  tenant_id: string
  doctor: AdminTenantDoctorItem
}

// ============================================================================
// Users / role distribution
// ============================================================================

export interface AdminUserItem {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  is_email_verified: boolean
  last_login_at: string | null
  tenant_id: string | null
  tenant_name: string | null
  created_at: string
}

export interface AdminUsersResponse {
  summary: {
    total: number
    by_role: {
      admin: number
      operator: number
      doctor: number
      receptionist: number
    }
  }
  users: AdminUserItem[]
}

export interface AdminUpdateUserRequest {
  role?: UserRole
  is_active?: boolean
}

export interface AdminUpdateUserResponse {
  message: string
  user: AdminUserItem
}

// ===== Work queue (GET /admin/dashboard/queue) =====

export interface QueueTenant {
  tenant_id: string
  clinic_name: string
  doctor_name: string | null
  email: string | null
  /** Registered (approvals) or listed itself (verification) */
  since: string
}

export interface AdminQueue {
  pending_approvals_total: number
  pending_approvals: QueueTenant[]
  verification_waiting_total: number
  verification_waiting: QueueTenant[]
  contact: {
    new: number
    by_topic: Record<string, number>
    latest: { id: string; topic: string; name: string; created_at: string }[]
  }
  marketing: { needs_draft: number; waiting_for_doctor: number; ready_to_post: number }
  revenue: {
    /** Decimal serialised as a string */
    this_month: string
    last_month: string
    paid_orders_this_month: number
    abandoned_checkouts: number
    failed_last_7_days: number
  }
  plans_expiring_total: number
  plans_expiring: { tenant_id: string; clinic_name: string; plan: string; expires_at: string; days_left: number }[]
  recently_expired: number
  growth: { new_tenants_this_month: number; new_tenants_last_month: number }
}
