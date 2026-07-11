/**
 * Medicine and Medicine Alias Types
 * Matches backend schemas from app/shared/schemas/medicine.py
 */

export type MedicalSystem = 'homeopathy' | 'ayurveda' | 'unani' | 'herbal';

export type MedicineAliasType =
  | 'transliteration'
  | 'common_name'
  | 'brand_name'
  | 'regional'
  | 'abbreviation';

// ===== Medicine Types =====

export interface MedicineBase {
  name_en: string;
  name_bn: string | null;
  system: MedicalSystem;
  category: string | null;
  description_en: string | null;
  description_bn: string | null;
  potency: string | null;
  dosage_guidance_en: string | null;
  dosage_guidance_bn: string | null;
  indications_en: string | null;
  indications_bn: string | null;
  contraindications_en: string | null;
  contraindications_bn: string | null;
  is_global: boolean;
  is_active: boolean;
}

export interface Medicine extends MedicineBase {
  id: number;
  tenant_id: string | null;
  created_at: string;
  updated_at: string | null;
  deleted_at: string | null;
}

export interface MedicineListItem {
  id: number;
  name_en: string;
  name_bn: string | null;
  system: MedicalSystem;
  category: string | null;
  potency: string | null;
  is_global: boolean;
  is_active: boolean;
}

export interface MedicineSearchResult {
  id: number;
  name_en: string;
  name_bn: string | null;
  system: MedicalSystem;
  potency: string | null;
  category: string | null;
  matched_alias: string | null;
  rank: number;
  // Optional fields present in full medicine but not guaranteed in search results
  is_global?: boolean;
  dosage_guidance_en?: string | null;
  indications_en?: string | null;
}

export interface MedicineCreate extends MedicineBase {}

export interface MedicineUpdate {
  name_en?: string;
  name_bn?: string | null;
  system?: MedicalSystem;
  category?: string | null;
  description_en?: string | null;
  description_bn?: string | null;
  potency?: string | null;
  dosage_guidance_en?: string | null;
  dosage_guidance_bn?: string | null;
  indications_en?: string | null;
  indications_bn?: string | null;
  contraindications_en?: string | null;
  contraindications_bn?: string | null;
  is_active?: boolean;
}

// ===== Medicine Alias Types =====

export interface MedicineAliasBase {
  alias_en: string | null;
  alias_bn: string | null;
  alias_type: MedicineAliasType;
  priority: number;
  is_active: boolean;
}

export interface MedicineAlias extends MedicineAliasBase {
  id: number;
  medicine_id: number;
  tenant_id: string | null;
  created_at: string;
}

export interface MedicineAliasCreate extends MedicineAliasBase {
  medicine_id: number;
}

export interface MedicineAliasUpdate {
  alias_en?: string | null;
  alias_bn?: string | null;
  alias_type?: MedicineAliasType;
  priority?: number;
  is_active?: boolean;
}

// ===== UI Helper Types =====

export interface MedicineFilters {
  system?: MedicalSystem;
  category?: string;
  is_global?: boolean;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}

export interface MedicineSearchParams {
  q: string;
  system?: MedicalSystem;
  limit?: number;
}
