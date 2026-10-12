/** Facebook profile promotion (matches backend app/shared/schemas/marketing.py). */

export type FbStatus = 'requested' | 'drafted' | 'approved' | 'posted' | 'rejected' | 'cancelled'

/** Statuses where someone still has to act; a clinic may have only one open request. */
export const FB_OPEN_STATUSES: FbStatus[] = ['requested', 'drafted', 'approved']

export interface FacebookRequest {
  id: string
  status: FbStatus
  /** What the doctor asked to highlight */
  doctor_note: string | null
  /** Staff's drafted post, shown to the doctor for approval */
  draft_text: string | null
  /** Doctor's reply when asking for changes (or an approval comment) */
  doctor_comment: string | null
  /** The exact text the doctor approved; frozen */
  approved_text: string | null
  reject_reason: string | null
  /** Link to the live Facebook post, once posted */
  post_url: string | null
  created_at: string
  drafted_at: string | null
  approved_at: string | null
  posted_at: string | null
}

/** Machine-readable reasons a new request is not possible right now. */
export type FbBlocker = 'not_in_plan' | 'no_public_profile' | 'quota_used' | 'open_request'

export interface FacebookSummary {
  /** Whether the clinic's plan includes the benefit (Pro and Enterprise) */
  in_plan: boolean
  /** Features per calendar quarter; null = unlimited */
  limit: number | null
  used: number
  remaining: number | null
  period_start: string
  period_end: string
  blockers: FbBlocker[]
  can_request: boolean
  /** Public profile path (e.g. /practitioners/dr-x) when the profile is live, else null */
  profile_path: string | null
  open_request: FacebookRequest | null
  history: FacebookRequest[]
}

export interface AdminFacebookRequest extends FacebookRequest {
  tenant_id: string
  tenant_name: string
  requester_name: string
  /** Public profile path if the profile is live right now */
  profile_path: string | null
}

/** 409/403 bodies: {code, message}. Codes include request_in_progress, no_public_profile,
 * not_cancellable, nothing_to_approve, nothing_to_change, not_draftable, not_rejectable, not_approved,
 * and (403) feature_not_in_plan / plan_limit_reached. */
export interface FacebookRefusal {
  code: string
  message: string
}
