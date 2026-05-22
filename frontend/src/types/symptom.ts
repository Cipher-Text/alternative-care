/**
 * Symptom and Symptom Alias Types
 * Matches backend schemas from app/shared/schemas/symptom.py
 */

export type SymptomAliasType =
  | 'transliteration'
  | 'common_name'
  | 'regional'
  | 'colloquial';

export type SymptomCategory =
  | 'neurological'
  | 'general'
  | 'respiratory'
  | 'digestive'
  | 'mental'
  | 'musculoskeletal'
  | 'skin'
  | 'immune'
  | 'cardiovascular'
  | 'metabolic'
  | 'reproductive'
  | 'ear_nose_throat';

// ===== Symptom Types =====

export interface SymptomBase {
  name_en: string;
  name_bn: string | null;
  description_en: string | null;
  description_bn: string | null;
  category: string | null;
  is_global: boolean;
  is_active: boolean;
}

export interface Symptom extends SymptomBase {
  id: number;
  tenant_id: string;
  created_at: string;
  updated_at: string | null;
}

export interface SymptomListItem {
  id: number;
  name_en: string;
  name_bn: string | null;
  category: string | null;
  is_global: boolean;
  is_active: boolean;
}

export interface SymptomSearchResult {
  symptom: Symptom;
  matched_term: string;
  match_type: 'exact' | 'alias' | 'fuzzy';
  relevance_score: number;
}

export interface SymptomCreate extends SymptomBase {}

export interface SymptomUpdate {
  name_en?: string;
  name_bn?: string | null;
  description_en?: string | null;
  description_bn?: string | null;
  category?: string | null;
  is_active?: boolean;
}

// ===== Symptom Alias Types =====

export interface SymptomAliasBase {
  alias_en: string | null;
  alias_bn: string | null;
  alias_type: SymptomAliasType;
  priority: number;
  is_active: boolean;
}

export interface SymptomAlias extends SymptomAliasBase {
  id: number;
  symptom_id: number;
  tenant_id: string;
  created_at: string;
  updated_at: string | null;
}

export interface SymptomAliasCreate extends SymptomAliasBase {
  symptom_id: number;
}

export interface SymptomAliasUpdate {
  alias_en?: string | null;
  alias_bn?: string | null;
  alias_type?: SymptomAliasType;
  priority?: number;
  is_active?: boolean;
}

// ===== UI Helper Types =====

export interface SymptomFilters {
  category?: string;
  is_global?: boolean;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export interface SymptomSearchParams {
  q: string;
  category?: string;
  limit?: number;
}
