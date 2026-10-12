import apiClient from './client'
import type { ClinicProfile } from '@/types/tenant'

export const tenantApi = {
  getProfile: async (): Promise<ClinicProfile> => (await apiClient.get('/tenant/profile')).data,
  /** Multipart upload; the server validates, resizes and re-encodes the image. */
  uploadLogo: async (file: File): Promise<ClinicProfile> => {
    const form = new FormData()
    form.append('file', file)
    // Let the browser set the multipart boundary (the client's default is JSON)
    return (await apiClient.post('/tenant/logo', form, { headers: { 'Content-Type': undefined } })).data
  },
  removeLogo: async (): Promise<ClinicProfile> => (await apiClient.delete('/tenant/logo')).data,
}
