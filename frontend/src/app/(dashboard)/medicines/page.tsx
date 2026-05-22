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
      } catch (error) {
        alert('Failed to delete medicine');
      }
    }
  };

  const getSystemColor = (system: MedicalSystem) => {
    switch (system) {
      case 'homeopathy':
        return 'bg-blue-100 text-blue-800';
      case 'ayurveda':
        return 'bg-green-100 text-green-800';
      case 'unani':
        return 'bg-purple-100 text-purple-800';
      case 'herbal':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
          <h1 className="text-3xl font-bold">Medicine Library</h1>
          <p className="text-gray-600 mt-2">
            Manage medicines for all systems
          </p>
        </div>
        <Button onClick={() => router.push('/medicines/new')}>
          <Plus className="w-4 h-4 mr-2" />
          Add Medicine
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search medicines..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Medical System</label>
            <Select
              value={filters.system || 'all'}
              onValueChange={(value) =>
                setFilters({ ...filters, system: value === 'all' ? undefined : value as MedicalSystem })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All Systems" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Systems</SelectItem>
                <SelectItem value="homeopathy">Homeopathy</SelectItem>
                <SelectItem value="ayurveda">Ayurveda</SelectItem>
                <SelectItem value="unani">Unani</SelectItem>
                <SelectItem value="herbal">Herbal</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Source</label>
            <Select
              value={filters.is_global === undefined ? 'all' : filters.is_global ? 'global' : 'tenant'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_global: value === 'all' ? undefined : value === 'global',
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All Sources" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                <SelectItem value="global">Global</SelectItem>
                <SelectItem value="tenant">My Medicines</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Status</label>
            <Select
              value={filters.is_active === undefined ? 'all' : filters.is_active ? 'active' : 'inactive'}
              onValueChange={(value) =>
                setFilters({
                  ...filters,
                  is_active: value === 'all' ? undefined : value === 'active',
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
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
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : !filteredMedicines || filteredMedicines.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500">No medicines found</p>
          <Button className="mt-4" onClick={() => router.push('/medicines/new')}>
            <Plus className="w-4 h-4 mr-2" />
            Add First Medicine
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMedicines.map((medicine) => (
            <Card key={medicine.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{medicine.name_en}</h3>
                  {medicine.name_bn && (
                    <p className="text-gray-600 text-sm">{medicine.name_bn}</p>
                  )}
                </div>
                {medicine.is_global && (
                  <Badge variant="outline" className="text-xs">
                    Global
                  </Badge>
                )}
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2">
                  <Badge className={getSystemColor(medicine.system)}>
                    {medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
                  </Badge>
                  {medicine.potency && (
                    <Badge variant="outline">{medicine.potency}</Badge>
                  )}
                </div>
                {medicine.category && (
                  <p className="text-sm text-gray-600">{medicine.category}</p>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
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
                      onClick={() => router.push(`/medicines/${medicine.id}/edit`)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(medicine.id)}
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
    </div>
  );
}
