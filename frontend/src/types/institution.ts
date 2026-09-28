/**
 * Institution catalog types
 * Matches backend schemas from app/shared/schemas/institution.py
 */

export type Discipline = 'homeopathy' | 'ayurveda' | 'unani' | 'herbal';
export type InstitutionType = 'government' | 'private';

export interface InstitutionBase {
  name_en: string;
  name_bn: string | null;
  institution_type: InstitutionType;
  disciplines: Discipline[];
  courses_offered: string | null;
  location: string | null;
  district_id: number | null;
  website_url: string | null;
  registration_code: string | null;
  source_url: string | null;
  is_active: boolean;
}

export interface Institution extends InstitutionBase {
  id: number;
  is_verified: boolean;
  verified_at: string | null;
  verified_by: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface InstitutionListItem {
  id: number;
  name_en: string;
  name_bn: string | null;
  institution_type: InstitutionType;
  disciplines: Discipline[];
  courses_offered: string | null;
  location: string | null;
  district_id: number | null;
  website_url: string | null;
  registration_code: string | null;
  source_url: string | null;
  is_verified: boolean;
  is_active: boolean;
}

export type InstitutionCreate = InstitutionBase;

export interface InstitutionUpdate {
  name_en?: string;
  name_bn?: string | null;
  institution_type?: InstitutionType;
  disciplines?: Discipline[];
  courses_offered?: string | null;
  location?: string | null;
  district_id?: number | null;
  website_url?: string | null;
  registration_code?: string | null;
  source_url?: string | null;
  is_active?: boolean;
  is_verified?: boolean;
}

export interface InstitutionFilters {
  discipline?: Discipline;
  institution_type?: InstitutionType;
  district_id?: number;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}
