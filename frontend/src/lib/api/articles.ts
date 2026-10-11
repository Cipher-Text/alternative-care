import { apiClient } from './client'
import type {
  Article,
  ArticleInput,
  ArticleListItem,
  ArticleStatus,
} from '@/types/article'

const BASE = '/articles'

/** Authoring API: doctors see their own articles, admins see all. */
export const articlesApi = {
  list: async (params?: { status?: ArticleStatus; limit?: number; offset?: number }): Promise<ArticleListItem[]> =>
    (await apiClient.get(BASE, { params })).data,
  get: async (id: string): Promise<Article> => (await apiClient.get(`${BASE}/${id}`)).data,
  create: async (data: ArticleInput): Promise<Article> => (await apiClient.post(BASE, data)).data,
  update: async (id: string, data: ArticleInput): Promise<Article> =>
    (await apiClient.patch(`${BASE}/${id}`, data)).data,
  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE}/${id}`)
  },
  submit: async (id: string): Promise<Article> => (await apiClient.post(`${BASE}/${id}/submit`)).data,
  /** Admin only. reviewer_display is the public credit, e.g. "Dr. A. Rahman, BHMS". */
  publish: async (id: string, data: { reviewer_display: string; review_due_at?: string }): Promise<Article> =>
    (await apiClient.post(`${BASE}/${id}/publish`, data)).data,
  /** Admin only. */
  returnToAuthor: async (id: string, review_note: string): Promise<Article> =>
    (await apiClient.post(`${BASE}/${id}/return`, { review_note })).data,
  /** Admin only. */
  unpublish: async (id: string): Promise<Article> => (await apiClient.post(`${BASE}/${id}/unpublish`)).data,
}
