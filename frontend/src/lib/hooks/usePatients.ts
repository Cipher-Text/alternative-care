import { useQuery, useMutation, useQueryClient } from 'react-query'
import { patientsApi, geographicApi } from '@/lib/api/patients'
import type {
  PatientCreateRequest,
  PatientUpdateRequest,
  PatientListParams,
} from '@/types/patient'
import { toast } from 'react-hot-toast'

export function usePatients(params?: PatientListParams) {
  return useQuery(['patients', params], () => patientsApi.list(params), {
    staleTime: 30000,
  })
}

export function usePatient(id: string) {
  return useQuery(['patient', id], () => patientsApi.get(id), {
    enabled: !!id,
    staleTime: 30000,
  })
}

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

// Patient tags
export function usePatientTags(patientId: string) {
  return useQuery(
    ['patient', patientId, 'tags'],
    () => patientsApi.getTags(patientId),
    { enabled: !!patientId }
  )
}

export function useAddPatientTag() {
  const queryClient = useQueryClient()

  return useMutation(
    ({
      patientId,
      data,
    }: {
      patientId: string
      data: Parameters<typeof patientsApi.addTag>[1]
    }) => patientsApi.addTag(patientId, data),
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
    ({ patientId, tagId }: { patientId: string; tagId: number }) =>
      patientsApi.deleteTag(tagId),
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
    { enabled: !!patientId }
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
      data: Parameters<typeof patientsApi.addDiagnosis>[1]
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
    staleTime: Infinity,
  })
}

export function useDistricts(divisionId: number | null) {
  return useQuery(
    ['districts', divisionId],
    () => geographicApi.getDistricts(divisionId!),
    {
      enabled: !!divisionId,
      staleTime: Infinity,
    }
  )
}

export function useUpazilas(districtId: number | null) {
  return useQuery(
    ['upazilas', districtId],
    () => geographicApi.getUpazilas(districtId!),
    {
      enabled: !!districtId,
      staleTime: Infinity,
    }
  )
}
