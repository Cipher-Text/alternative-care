/**
 * API Types - Common types for API requests and responses
 */

/**
 * Pydantic validation error from FastAPI
 */
export interface ValidationError {
  type: string
  loc: (string | number)[]
  msg: string
  input?: unknown
  ctx?: Record<string, unknown>
}

/**
 * Standard API error response from backend
 */
export interface APIError {
  detail: string | ValidationError[]
  status?: number
}

/**
 * Axios error with API error response
 */
export interface AxiosAPIError extends Error {
  response?: {
    data?: APIError
    status: number
  }
  request?: unknown
  config?: unknown
}

/**
 * Type guard to check if error is an Axios API error
 */
export function isAxiosAPIError(error: unknown): error is AxiosAPIError {
  return (
    error !== null &&
    typeof error === 'object' &&
    'response' in error &&
    typeof (error as AxiosAPIError).response === 'object'
  )
}

/**
 * Extract error message from unknown error
 */
export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (isAxiosAPIError(error)) {
    const detail = error.response?.data?.detail

    // Handle string detail (normal error)
    if (typeof detail === 'string') {
      return detail
    }

    // Handle array of validation errors (Pydantic)
    if (Array.isArray(detail) && detail.length > 0) {
      // Return the first error message
      const firstError = detail[0] as ValidationError
      return firstError.msg || fallback
    }

    return fallback
  }
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return fallback
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  skip?: number
  limit?: number
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
