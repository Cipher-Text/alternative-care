import { useQuery, useMutation, useQueryClient } from 'react-query'
import { patientsApi, geographicApi } from '@/lib/api/patients'
import type {
  Patient,
  PatientCreateRequest,
  PatientUpdateRequest,
  PatientListParams,
} from '@/types/patient'
import { toast } from 'react-hot-toast'

// List patients
export function usePatients(params?: PatientListParams) {
  return useQuery(['patients', params], () => patientsApi.list(params), {
    staleTime: 30000, // 30 seconds
  })
}

// Get single patient
export function usePatient(id: string) {
  return useQuery(['patient', id], () => patientsApi.get(id), {
    enabled: !!id,
    staleTime: 30000,
  })
}

// Create patient
export function useCreatePatient() {
  const queryClient = useQueryClient()

  return useMutation(
    (data: PatientCreateRequest) => patientsApi.create(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('patients')
        toast.success('Patient created successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create patient')
      },
    }
  )
}

// Update patient
export function useUpdatePatient() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: string; data: PatientUpdateRequest }) =>
      patientsApi.update(id, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries('patients')
        queryClient.invalidateQueries(['patient', variables.id])
        toast.success('Patient updated successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update patient')
      },
    }
  )
}

// Delete patient
export function useDeletePatient() {
  const queryClient = useQueryClient()

  return useMutation((id: string) => patientsApi.delete(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('patients')
      toast.success('Patient deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete patient')
    },
  })
}

// Search patients
export function useSearchPatients(query: string) {
  return useQuery(
    ['patients', 'search', query],
    () => patientsApi.search(query),
    {
      enabled: query.length > 0,
      staleTime: 10000,
    }
  )
}

// Patient tags
export function usePatientTags(patientId: string) {
  return useQuery(
    ['patient', patientId, 'tags'],
    () => patientsApi.getTags(patientId),
    {
      enabled: !!patientId,
    }
  )
}

export function useAddPatientTag() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ patientId, tag }: { patientId: string; tag: string }) =>
      patientsApi.addTag(patientId, tag),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['patient', variables.patientId, 'tags'])
        toast.success('Tag added')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to add tag')
      },
    }
  )
}

export function useDeletePatientTag() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ patientId, tagId }: { patientId: string; tagId: string }) =>
      patientsApi.deleteTag(patientId, tagId),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['patient', variables.patientId, 'tags'])
        toast.success('Tag removed')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to remove tag')
      },
    }
  )
}

// Patient diagnoses
export function usePatientDiagnoses(patientId: string) {
  return useQuery(
    ['patient', patientId, 'diagnoses'],
    () => patientsApi.getDiagnoses(patientId),
    {
      enabled: !!patientId,
    }
  )
}

export function useAddPatientDiagnosis() {
  const queryClient = useQueryClient()

  return useMutation(
    ({
      patientId,
      data,
    }: {
      patientId: string
      data: { diagnosis: string; diagnosed_at?: string; notes?: string }
    }) => patientsApi.addDiagnosis(patientId, data),
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries(['patient', variables.patientId, 'diagnoses'])
        toast.success('Diagnosis added')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to add diagnosis')
      },
    }
  )
}

// Geographic hooks
export function useDivisions() {
  return useQuery('divisions', geographicApi.getDivisions, {
    staleTime: Infinity, // Divisions rarely change
  })
}

export function useDistricts(divisionId: string) {
  return useQuery(
    ['districts', divisionId],
    () => geographicApi.getDistricts(divisionId),
    {
      enabled: !!divisionId,
      staleTime: Infinity,
    }
  )
}

export function useUpazilas(districtId: string) {
  return useQuery(
    ['upazilas', districtId],
    () => geographicApi.getUpazilas(districtId),
    {
      enabled: !!districtId,
      staleTime: Infinity,
    }
  )
}
