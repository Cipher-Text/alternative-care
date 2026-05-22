/**
 * Medicines List Page
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMedicines, useDeleteMedicine } from '@/lib/hooks/useMedicines';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Search, Trash2, Edit, Eye } from 'lucide-react';
import type { MedicalSystem, MedicineFilters } from '@/types/medicine';

export default function MedicinesPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<MedicineFilters>({
    is_active: true,
    limit: 100,
  });
  const [searchTerm, setSearchTerm] = useState('');

  const { data: medicines, isLoading } = useMedicines(filters);
  const deleteMedicine = useDeleteMedicine();

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this medicine?')) {
      try {
        await deleteMedicine.mutateAsync(id);
      } catch {
        alert('Failed to delete medicine');
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

  // Filter medicines by search term (client-side)
  const filteredMedicines = medicines?.filter((med) =>
    med.name_en.toLowerCase().includes(searchTerm.toLowerCase()) ||
    med.name_bn?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Medicine Library</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage medicines for all systems
          </p>
        </div>
        <Button
          onClick={() => router.push('/medicines/new')}
          className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/50"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Medicine
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6 bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                placeholder="Search medicines..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder:text-gray-500"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">Medical System</label>
            <Select
              value={filters.system || 'all'}
              onValueChange={(value) =>
                setFilters({ ...filters, system: value === 'all' ? undefined : value as MedicalSystem })
              }
            >
              <SelectTrigger className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder="All Systems" />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">All Systems</SelectItem>
                <SelectItem value="homeopathy">Homeopathy</SelectItem>
                <SelectItem value="ayurveda">Ayurveda</SelectItem>
                <SelectItem value="unani">Unani</SelectItem>
                <SelectItem value="herbal">Herbal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">Source</label>
            <Select
              value={filters.is_global === undefined ? 'all' : filters.is_global ? 'global' : 'tenant'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_global: value === 'all' ? undefined : value === 'global',
                })
              }
            >
              <SelectTrigger className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder="All Sources" />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="global">Global</SelectItem>
                <SelectItem value="tenant">My Medicines</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block text-gray-700 dark:text-gray-300">Status</label>
            <Select
              value={filters.is_active === undefined ? 'all' : filters.is_active ? 'active' : 'inactive'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_active: value === 'all' ? undefined : value === 'active',
                })
              }
            >
              <SelectTrigger className="bg-white dark:bg-slate-900 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent className="bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 text-gray-900 dark:text-white">
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Medicine List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 dark:text-indigo-400" />
        </div>
      ) : !filteredMedicines || filteredMedicines.length === 0 ? (
        <Card className="p-12 text-center bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700">
          <p className="text-gray-600 dark:text-gray-400">No medicines found</p>
          <Button
            className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white"
            onClick={() => router.push('/medicines/new')}
          >
            <Plus className="w-4 h-4 mr-2" />
            Add First Medicine
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedicines.map((medicine) => (
            <Card
              key={medicine.id}
              className="p-6 bg-white dark:bg-slate-800/50 border-gray-200 dark:border-slate-700 hover:shadow-lg dark:hover:shadow-xl dark:hover:shadow-indigo-500/10 hover:border-gray-300 dark:hover:border-slate-600 transition-all duration-200"
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
                    className="text-xs bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
                  >
                    Global
                  </Badge>
                )}
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge className={getSystemColor(medicine.system)}>
                    {medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
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
                  className="flex-1 bg-white dark:bg-slate-700/50 border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-200 hover:bg-indigo-50 dark:hover:bg-indigo-600 hover:text-indigo-700 dark:hover:text-white hover:border-indigo-300 dark:hover:border-indigo-600"
                  onClick={() => router.push(`/medicines/${medicine.id}`)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  View
                </Button>
                {!medicine.is_global && (
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
    </div>
  );
}
