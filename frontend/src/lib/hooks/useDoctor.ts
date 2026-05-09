import { useQuery, useMutation, useQueryClient } from 'react-query'
import { doctorApi } from '@/lib/api/doctor'
import type {
  DoctorProfileUpdate,
  DoctorDegreeCreate,
  DoctorDegreeUpdate,
  DoctorTrainingCreate,
  DoctorTrainingUpdate,
} from '@/types/doctor'
import { toast } from 'react-hot-toast'

// ===== Profile Hooks =====

export function useDoctorProfile() {
  return useQuery('doctorProfile', () => doctorApi.getProfile(), {
    staleTime: 60000, // 1 minute
  })
}

export function useUpdateDoctorProfile() {
  const queryClient = useQueryClient()

  return useMutation((data: DoctorProfileUpdate) => doctorApi.updateProfile(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('doctorProfile')
      toast.success('Profile updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    },
  })
}

// ===== Degree Hooks =====

export function useDoctorDegrees() {
  return useQuery('doctorDegrees', () => doctorApi.listDegrees(), {
    staleTime: 60000,
  })
}

export function useDoctorDegree(id: number) {
  return useQuery(['doctorDegree', id], () => doctorApi.getDegree(id), {
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useCreateDoctorDegree() {
  const queryClient = useQueryClient()

  return useMutation((data: DoctorDegreeCreate) => doctorApi.createDegree(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('doctorDegrees')
      toast.success('Degree added successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add degree')
    },
  })
}

export function useUpdateDoctorDegree() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: number; data: DoctorDegreeUpdate }) =>
      doctorApi.updateDegree(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('doctorDegrees')
        toast.success('Degree updated successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update degree')
      },
    }
  )
}

export function useDeleteDoctorDegree() {
  const queryClient = useQueryClient()

  return useMutation((id: number) => doctorApi.deleteDegree(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('doctorDegrees')
      toast.success('Degree deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete degree')
    },
  })
}

// ===== Training Hooks =====

export function useDoctorTrainings(activeOnly?: boolean) {
  return useQuery(
    ['doctorTrainings', activeOnly],
    () => doctorApi.listTrainings(activeOnly),
    {
      staleTime: 60000,
    }
  )
}

export function useDoctorTraining(id: number) {
  return useQuery(['doctorTraining', id], () => doctorApi.getTraining(id), {
    enabled: !!id,
    staleTime: 60000,
  })
}

export function useCreateDoctorTraining() {
  const queryClient = useQueryClient()

  return useMutation((data: DoctorTrainingCreate) => doctorApi.createTraining(data), {
    onSuccess: () => {
      queryClient.invalidateQueries('doctorTrainings')
      toast.success('Training added successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add training')
    },
  })
}

export function useUpdateDoctorTraining() {
  const queryClient = useQueryClient()

  return useMutation(
    ({ id, data }: { id: number; data: DoctorTrainingUpdate }) =>
      doctorApi.updateTraining(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('doctorTrainings')
        toast.success('Training updated successfully')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update training')
      },
    }
  )
}

export function useDeleteDoctorTraining() {
  const queryClient = useQueryClient()

  return useMutation((id: number) => doctorApi.deleteTraining(id), {
    onSuccess: () => {
      queryClient.invalidateQueries('doctorTrainings')
      toast.success('Training deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete training')
    },
  })
}
