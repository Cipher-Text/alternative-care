/**
 * Medicines List Page
 */

'use client';

import { useTranslations } from 'next-intl'
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMedicines, useDeleteMedicine, useSearchMedicines } from '@/lib/hooks/useMedicines';
import { Pager, clientPage, serverPage, usePager } from '@/components/shared/Pager';
import { useCan } from '@/lib/auth/permissions';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Search, Trash2, Edit, Eye } from 'lucide-react';
import type { MedicalSystem, MedicineFilters } from '@/types/medicine';

export default function MedicinesPage() {
  const tp = useTranslations('pages');
  const t = useTranslations('libUi');
  const ts = useTranslations('libSystemUi');
  const router = useRouter();
  const can = useCan();
  const [filters, setFilters] = useState<MedicineFilters>({
    is_active: true,
  });
  const [searchTerm, setSearchTerm] = useState('');

  // Debounce the search box, then query GET /medicines/search (names + aliases, ranked)
  const [debouncedTerm, setDebouncedTerm] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedTerm(searchTerm.trim()), 300);
    return () => clearTimeout(t);
  }, [searchTerm]);
  const isSearching = debouncedTerm.length > 0;

  const pager = usePager(undefined, [filters, debouncedTerm]);

  // Browsing pages on the server (one extra row tells us a next page exists)
  const { data: listedRows, isLoading: listLoading } = useMedicines(
    { ...filters, limit: pager.pageSize + 1, offset: pager.offset },
    { keepPreviousData: true }
  );
  const { items: listed, hasNext: listHasNext } = serverPage(listedRows, pager.pageSize);
  // Search returns the top-ranked matches (no offset), so those are paged in the browser
  const { data: searched, isLoading: searchLoading } = useSearchMedicines({
    q: debouncedTerm,
    system: filters.system,
    limit: 100,
  });
  const isLoading = isSearching ? searchLoading : listLoading;
  const deleteMedicine = useDeleteMedicine();

  const handleDelete = async (id: number) => {
    if (confirm(t('confirmDelete'))) {
      try {
        await deleteMedicine.mutateAsync(id);
      } catch {
        alert(t('deleteFailed'));
      }
    }
  };

  const getSystemColor = (system: MedicalSystem) => {
    switch (system) {
      case 'homeopathy':
        return 'bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-500/20 dark:text-blue-300 dark:border-blue-500/30';
      case 'ayurveda':
        return 'bg-green-100 text-green-700 border border-green-200 dark:bg-green-500/20 dark:text-green-300 dark:border-green-500/30';
      case 'unani':
        return 'bg-purple-100 text-purple-700 border border-purple-200 dark:bg-purple-500/20 dark:text-purple-300 dark:border-purple-500/30';
      case 'herbal':
        return 'bg-orange-100 text-orange-700 border border-orange-200 dark:bg-orange-500/20 dark:text-orange-300 dark:border-orange-500/30';
      default:
        return 'bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-500/20 dark:text-gray-300 dark:border-gray-500/30';
    }
  };

  // Search results omit is_active/is_global, so default them for display and apply the
  // Source filter client-side; the system filter is already applied by the API.
  const searchMatches = isSearching
    ? (searched ?? [])
        .map((m) => ({ ...m, is_global: m.is_global ?? false, is_active: true }))
        .filter((m) => filters.is_global === undefined || m.is_global === filters.is_global)
    : [];
  const searchPage = clientPage(searchMatches, pager.page, pager.pageSize);
  const filteredMedicines = isSearching ? searchPage.items : listed;
  const hasNext = isSearching ? searchPage.hasNext : listHasNext;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{tp('medicinesTitle')}</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {tp('medicinesSubtitle')}
          </p>
        </div>
        {can.writeClinical && (
          <Button
            onClick={() => router.push('/medicines/new')}
            className="bg-primary hover:bg-slate-950 dark:hover:bg-emerald-800 text-white shadow-lg shadow-slate-900/10"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('addMedicine')}
          </Button>
        )}
      </div>

      {/* Filters */}
      <Card className="p-6 bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">{t('search')}</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                aria-label={t('searchAria')}
                placeholder={t('searchPlaceholder')}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder:text-gray-500"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">{t('medicalSystem')}</label>
            <Select
              value={filters.system || 'all'}
              onValueChange={(value) =>
                setFilters({ ...filters, system: value === 'all' ? undefined : value as MedicalSystem })
              }
            >
              <SelectTrigger aria-label={t('medicalSystem')} className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder={t('allSystems')} />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">{t('allSystems')}</SelectItem>
                <SelectItem value="homeopathy">{ts('homeopathy')}</SelectItem>
                <SelectItem value="ayurveda">{ts('ayurveda')}</SelectItem>
                <SelectItem value="unani">{ts('unani')}</SelectItem>
                <SelectItem value="herbal">{ts('herbal')}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">{t('source')}</label>
            <Select
              value={filters.is_global === undefined ? 'all' : filters.is_global ? 'global' : 'tenant'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_global: value === 'all' ? undefined : value === 'global',
                })
              }
            >
              <SelectTrigger aria-label={t('source')} className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder={t('allSources')} />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">{t('allSources')}</SelectItem>
                <SelectItem value="global">{t('global')}</SelectItem>
                <SelectItem value="tenant">{t('myMedicines')}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">{t('status')}</label>
            <Select
              value={filters.is_active === undefined ? 'all' : filters.is_active ? 'active' : 'inactive'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_active: value === 'all' ? undefined : value === 'active',
                })
              }
            >
              <SelectTrigger aria-label={t('status')} className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder={t('allStatuses')} />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">{t('allStatuses')}</SelectItem>
                <SelectItem value="active">{t('active')}</SelectItem>
                <SelectItem value="inactive">{t('inactive')}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Medicine List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 dark:text-emerald-400" />
        </div>
      ) : !filteredMedicines || filteredMedicines.length === 0 ? (
        <Card className="p-12 text-center bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
          <p className="text-gray-600 dark:text-gray-400">{t('noneFound')}</p>
          {can.writeClinical && (
          <Button
            className="mt-4 bg-primary hover:bg-slate-950 dark:hover:bg-emerald-800 text-white"
            onClick={() => router.push('/medicines/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            {t('addFirst')}
          </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedicines.map((medicine) => (
            <Card
              key={medicine.id}
              className="p-6 bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-md dark:hover:shadow-md dark:hover:shadow-emerald-500/10 hover:border-gray-300 dark:hover:border-slate-600 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-1">
                    {medicine.name_en}
                  </h3>
                  {medicine.name_bn && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm">{medicine.name_bn}</p>
                  )}
                </div>
                {medicine.is_global && (
                  <Badge
                    variant="outline"
                    className="text-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                  >
                    {t('global')}
                  </Badge>
                )}
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className={getSystemColor(medicine.system)}>
                    {ts.has(medicine.system) ? ts(medicine.system) : medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
                  </Badge>
                  {medicine.potency && (
                    <Badge
                      variant="outline"
                      className="bg-gray-100 dark:bg-slate-700/50 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-slate-600"
                    >
                      {medicine.potency}
                    </Badge>
                  )}
                </div>
                {medicine.category && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                    {medicine.category}
                  </p>
                )}
              </div>

              <div className="flex gap-2 pt-2 border-t border-gray-200 dark:border-slate-700">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-emerald-50 dark:hover:bg-primary hover:text-emerald-700 dark:hover:text-white hover:border-emerald-300 dark:hover:border-emerald-600"
                  onClick={() => router.push(`/medicines/${medicine.id}`)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  {t('view')}
                </Button>
                {!medicine.is_global && can.writeClinical && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      className="bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-blue-600 hover:text-blue-700 dark:hover:text-white hover:border-blue-300 dark:hover:border-blue-600"
                      onClick={() => router.push(`/medicines/${medicine.id}/edit`)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(medicine.id)}
                      className="bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-600 hover:text-red-700 dark:hover:text-white hover:border-red-300 dark:hover:border-red-600"
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
        count={filteredMedicines?.length ?? 0}
        hasNext={hasNext}
        onPageChange={pager.setPage}
        total={isSearching ? searchPage.total : undefined}
        noun="medicines"
      />
    </div>
  );
}
