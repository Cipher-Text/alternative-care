/**
 * Symptoms List Page
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSymptoms, useDeleteSymptom } from '@/lib/hooks/useSymptoms';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Search, Trash2, Edit, Eye } from 'lucide-react';
import type { SymptomCategory, SymptomFilters } from '@/types/symptom';

export default function SymptomsPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<SymptomFilters>({
    is_active: true,
    limit: 100,
  });
  const [searchTerm, setSearchTerm] = useState('');

  const { data: symptoms, isLoading } = useSymptoms(filters);
  const deleteSymptom = useDeleteSymptom();

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this symptom?')) {
      try {
        await deleteSymptom.mutateAsync(id);
      } catch (error) {
        alert('Failed to delete symptom');
      }
    }
  };

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
      cardiovascular: 'bg-indigo-100 text-indigo-800',
      metabolic: 'bg-teal-100 text-teal-800',
      reproductive: 'bg-rose-100 text-rose-800',
      ear_nose_throat: 'bg-cyan-100 text-cyan-800',
      urinary: 'bg-violet-100 text-violet-800',
    };

    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  // Filter symptoms by search term (client-side)
  const filteredSymptoms = symptoms?.filter((symptom) =>
    symptom.name_en.toLowerCase().includes(searchTerm.toLowerCase()) ||
    symptom.name_bn?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Symptom Library</h1>
          <p className="text-gray-600 mt-2">
            Manage symptoms catalog
          </p>
        </div>
        <Button onClick={() => router.push('/symptoms/new')}>
          <Plus className="w-4 h-4 mr-2" />
          Add Symptom
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
                placeholder="Search symptoms..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Category</label>
            <Select
              value={filters.category || 'all'}
              onValueChange={(value) =>
                setFilters({ ...filters, category: value === 'all' ? undefined : value as SymptomCategory })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="neurological">Neurological</SelectItem>
                <SelectItem value="respiratory">Respiratory</SelectItem>
                <SelectItem value="digestive">Digestive</SelectItem>
                <SelectItem value="mental">Mental</SelectItem>
                <SelectItem value="musculoskeletal">Musculoskeletal</SelectItem>
                <SelectItem value="skin">Skin</SelectItem>
                <SelectItem value="immune">Immune</SelectItem>
                <SelectItem value="cardiovascular">Cardiovascular</SelectItem>
                <SelectItem value="metabolic">Metabolic</SelectItem>
                <SelectItem value="reproductive">Reproductive</SelectItem>
                <SelectItem value="ear_nose_throat">Ear/Nose/Throat</SelectItem>
                <SelectItem value="urinary">Urinary</SelectItem>
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
                <SelectItem value="tenant">My Symptoms</SelectItem>
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

      {/* Symptom List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : !filteredSymptoms || filteredSymptoms.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500">No symptoms found</p>
          <Button className="mt-4" onClick={() => router.push('/symptoms/new')}>
            <Plus className="w-4 h-4 mr-2" />
            Add First Symptom
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSymptoms.map((symptom) => (
            <Card key={symptom.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{symptom.name_en}</h3>
                  {symptom.name_bn && (
                    <p className="text-gray-600 text-sm">{symptom.name_bn}</p>
                  )}
                </div>
                {symptom.is_global && (
                  <Badge variant="outline" className="text-xs">
                    Global
                  </Badge>
                )}
              </div>

              <div className="space-y-2 mb-4">
                {symptom.category && (
                  <Badge className={getCategoryColor(symptom.category)}>
                    {symptom.category.split('_').map(word =>
                      word.charAt(0).toUpperCase() + word.slice(1)
                    ).join(' ')}
                  </Badge>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => router.push(`/symptoms/${symptom.id}`)}
                >
                  <Eye className="w-4 h-4 mr-1" />
                  View
                </Button>
                {!symptom.is_global && (
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
    </div>
  );
}
