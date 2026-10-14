/**
 * Symptoms List Page
 */

'use client';

import { useTranslations } from 'next-intl'
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSymptoms, useSearchSymptoms, useDeleteSymptom } from '@/lib/hooks/useSymptoms';
import { useDebouncedValue } from '@/lib/hooks/useDebouncedValue';
import { Pager, clientPage, serverPage, usePager } from '@/components/shared/Pager';
import { useCan } from '@/lib/auth/permissions';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Search, Trash2, Edit, Eye } from 'lucide-react';
import type { SymptomCategory, SymptomFilters } from '@/types/symptom';

export default function SymptomsPage() {
  const tp = useTranslations('pages');
  const t = useTranslations('symptomsUi');
  const tc = useTranslations('symptomCategoryUi');
  const router = useRouter();
  const { can } = useCan()
  const [filters, setFilters] = useState<SymptomFilters>({
    is_active: true,
  });
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedTerm = useDebouncedValue(searchTerm.trim());
  const isSearching = debouncedTerm.length > 0;
  const pager = usePager(undefined, [filters, debouncedTerm]);

  // Browsing pages on the server (one extra row tells us a next page exists)
  const { data: listedRows, isLoading: listLoading } = useSymptoms(
    { ...filters, limit: pager.pageSize + 1, offset: pager.offset },
    { keepPreviousData: true }
  );
  const { items: listed, hasNext: listHasNext } = serverPage(listedRows, pager.pageSize);
  // Search returns the top-ranked matches (no offset), so those are paged in the browser
  const { data: searched, isLoading: searchLoading } = useSearchSymptoms({
    q: debouncedTerm,
    category: filters.category,
    limit: 100,
  });
  const isLoading = isSearching ? searchLoading : listLoading;
  const deleteSymptom = useDeleteSymptom();

  const handleDelete = async (id: number) => {
    if (confirm(t('confirmDelete'))) {
      try {
        await deleteSymptom.mutateAsync(id);
      } catch (error) {
        alert(t('deleteFailed'));
      }
    }
  };

  const catLabel = (c: string) =>
    tc.has(`badge.${c}`)
      ? tc(`badge.${c}`)
      : c.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

  const getCategoryColor = (category: string | null) => {
    if (!category) return 'bg-gray-100 text-gray-800';

    const colors: Record<string, string> = {
      neurological: 'bg-purple-100 text-purple-800',
      respiratory: 'bg-blue-100 text-blue-800',
      digestive: 'bg-green-100 text-green-800',
      mental: 'bg-pink-100 text-pink-800',
      musculoskeletal: 'bg-orange-100 text-orange-800',
      skin: 'bg-yellow-100 text-yellow-800',
      immune: 'bg-red-100 text-red-800',
      cardiovascular: 'bg-emerald-100 text-emerald-800',
      metabolic: 'bg-teal-100 text-teal-800',
      reproductive: 'bg-rose-100 text-rose-800',
      ear_nose_throat: 'bg-cyan-100 text-cyan-800',
      urinary: 'bg-violet-100 text-violet-800',
    };

    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const searchMatches = isSearching ? (searched ?? []).map((r) => r.symptom) : [];
  const searchPage = clientPage(searchMatches, pager.page, pager.pageSize);
  const filteredSymptoms = isSearching ? searchPage.items : listed;
  const hasNext = isSearching ? searchPage.hasNext : listHasNext;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">{tp('symptomsTitle')}</h1>
          <p className="text-gray-600 mt-2">
            {tp('symptomsSubtitle')}
          </p>
        </div>
        {can('symptoms.write') && (
          <Button onClick={() => router.push('/symptoms/new')}>
            <Plus className="w-4 h-4 mr-2" />
            {t('addSymptom')}
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">{t('search')}</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                aria-label={t('searchAria')}
                placeholder={t('searchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">{t('category')}</label>
            <Select
              value={filters.category || 'all'}
              onValueChange={(value) =>
                setFilters({ ...filters, category: value === 'all' ? undefined : value as SymptomCategory })
              }
            >
              <SelectTrigger aria-label={t('category')}>
                <SelectValue placeholder={t('allCategories')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allCategories')}</SelectItem>
                {['neurological','respiratory','digestive','mental','musculoskeletal','skin','immune','cardiovascular','metabolic','reproductive','ear_nose_throat','urinary'].map((c) => (
                  <SelectItem key={c} value={c}>{tc(c)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">{t('source')}</label>
            <Select
              value={filters.is_global === undefined ? 'all' : filters.is_global ? 'global' : 'tenant'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_global: value === 'all' ? undefined : value === 'global',
                })
              }
            >
              <SelectTrigger aria-label={t('source')}>
                <SelectValue placeholder={t('allSources')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allSources')}</SelectItem>
                <SelectItem value="global">{t('global')}</SelectItem>
                <SelectItem value="tenant">{t('mySymptoms')}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">{t('status')}</label>
            <Select
              value={filters.is_active === undefined ? 'all' : filters.is_active ? 'active' : 'inactive'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_active: value === 'all' ? undefined : value === 'active',
                })
              }
            >
              <SelectTrigger aria-label={t('status')}>
                <SelectValue placeholder={t('allStatuses')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('allStatuses')}</SelectItem>
                <SelectItem value="active">{t('active')}</SelectItem>
                <SelectItem value="inactive">{t('inactive')}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Symptom List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : filteredSymptoms.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500">{t('noneFound')}</p>
          {can('symptoms.write') && (
          <Button className="mt-4" onClick={() => router.push('/symptoms/new')}>
            <Plus className="w-4 h-4 mr-2" />
            {t('addFirst')}
          </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSymptoms.map((symptom) => (
            <Card key={symptom.id} className="p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{symptom.name_en}</h3>
                  {symptom.name_bn && (
                    <p className="text-gray-600 text-sm">{symptom.name_bn}</p>
                  )}
                </div>
                {symptom.is_global && (
                  <Badge variant="outline" className="text-xs">
                    {t('global')}
                  </Badge>
                )}
              </div>

              <div className="space-y-2 mb-4">
                {symptom.category && (
                  <Badge className={getCategoryColor(symptom.category)}>
                    {catLabel(symptom.category)}
                  </Badge>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => router.push(`/symptoms/${symptom.id}`)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  {t('view')}
                </Button>
                {!symptom.is_global && can('symptoms.write') && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/symptoms/${symptom.id}/edit`)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(symptom.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Pager
        page={pager.page}
        pageSize={pager.pageSize}
        count={filteredSymptoms.length}
        hasNext={hasNext}
        onPageChange={pager.setPage}
        total={isSearching ? searchPage.total : undefined}
        noun="symptoms"
      />
    </div>
  );
}
