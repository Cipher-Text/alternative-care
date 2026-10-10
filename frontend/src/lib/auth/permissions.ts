import { useAuthStore } from '@/store/authStore'

/**
 * What the signed-in user's role may do in the UI. This only hides controls that the backend
 * would reject anyway (docs/architecture/roles-access.md); the server remains the authority.
 *
 * Receptionist: read-only on clinical records (patients, prescriptions, medicine/symptom
 * library), full on appointments and payments, no doctor profile or settings.
 */
export function useCan() {
  const role = useAuthStore((state) => state.user?.role)
  const isReceptionist = role === 'receptionist'

  return {
    isReceptionist,
    /** create/edit/delete patients, prescriptions, medicines, symptoms */
    writeClinical: !isReceptionist,
    /** doctor profile, integrations and other settings */
    manageClinicSettings: !isReceptionist,
  }
}
