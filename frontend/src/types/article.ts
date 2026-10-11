/** Editorial content (matches backend app/shared/schemas/article.py). */

export type ArticleKind = 'article' | 'video'
export type ArticleDiscipline = 'general' | 'homeopathy' | 'ayurveda' | 'unani' | 'herbal'
export type EvidenceLabel = 'general_info' | 'traditional_use' | 'limited_evidence' | 'studied'
export type ArticleStatus = 'draft' | 'in_review' | 'published'

export const ARTICLE_DISCIPLINES: ArticleDiscipline[] = ['general', 'homeopathy', 'ayurveda', 'unani', 'herbal']
export const EVIDENCE_LABELS: EvidenceLabel[] = ['general_info', 'traditional_use', 'limited_evidence', 'studied']

/** Full article as seen by authors and admins. */
export interface Article {
  id: string
  slug: string
  kind: ArticleKind
  discipline: ArticleDiscipline
  evidence_label: EvidenceLabel
  status: ArticleStatus
  title_en: string | null
  title_bn: string | null
  summary_en: string | null
  summary_bn: string | null
  body_en: string | null
  body_bn: string | null
  youtube_id: string | null
  author_id: string
  author_name: string
  reviewer_display: string | null
  reviewed_at: string | null
  review_note: string | null
  review_due_at: string | null
  review_overdue: boolean
  published_at: string | null
  created_at: string
  updated_at: string | null
}

export interface ArticleListItem {
  id: string
  slug: string
  kind: ArticleKind
  discipline: ArticleDiscipline
  status: ArticleStatus
  title_en: string | null
  title_bn: string | null
  author_name: string
  review_overdue: boolean
  updated_at: string | null
  created_at: string
}

export interface ArticleInput {
  kind?: ArticleKind
  discipline?: ArticleDiscipline
  evidence_label?: EvidenceLabel
  title_en?: string | null
  title_bn?: string | null
  summary_en?: string | null
  summary_bn?: string | null
  body_en?: string | null
  body_bn?: string | null
  /** A YouTube link or an 11-character video id */
  video_url?: string | null
  slug?: string
}

/** Published item as shown on the public site (no body). */
export interface PublicArticleItem {
  slug: string
  kind: ArticleKind
  discipline: ArticleDiscipline
  evidence_label: EvidenceLabel
  title_en: string | null
  title_bn: string | null
  summary_en: string | null
  summary_bn: string | null
  youtube_id: string | null
  author_name: string
  published_at: string | null
}

export interface PublicArticle extends PublicArticleItem {
  body_en: string | null
  body_bn: string | null
  reviewer_display: string | null
  reviewed_at: string | null
  review_due_at: string | null
}
