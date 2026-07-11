/**
 * Symptom Detail Page
 */

'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSymptom, useSymptomAliases, useDeleteSymptom, useCreateSymptomAlias, useDeleteSymptomAlias } from '@/lib/hooks/useSymptoms';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, ArrowLeft, Edit, Trash2, Plus, X } from 'lucide-react';
import type { SymptomAliasType } from '@/types/symptom';

export default function SymptomDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const symptomId = parseInt(id);

  const { data: symptom, isLoading } = useSymptom(symptomId);
  const { data: aliases = [] } = useSymptomAliases(symptomId);
  const deleteSymptom = useDeleteSymptom();
  const createAlias = useCreateSymptomAlias();
  const deleteAlias = useDeleteSymptomAlias();

  const [showAddAlias, setShowAddAlias] = useState(false);
  const [aliasForm, setAliasForm] = useState({
    alias_en: '',
    alias_type: '' as SymptomAliasType,
  });

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this symptom?')) {
      try {
        await deleteSymptom.mutateAsync(symptomId);
        router.push('/symptoms');
      } catch (error) {
        alert('Failed to delete symptom');
      }
    }
  };

  const handleAddAlias = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aliasForm.alias_en.trim() || !aliasForm.alias_type) return;

    try {
      await createAlias.mutateAsync({
        symptomId,
        payload: {
          alias_en: aliasForm.alias_en,
          alias_bn: null,
          alias_type: aliasForm.alias_type,
          symptom_id: symptomId,
          priority: 1,
          is_active: true,
        },
      });
      setAliasForm({ alias_en: '', alias_type: '' as SymptomAliasType });
      setShowAddAlias(false);
    } catch (error) {
      alert('Failed to add alias');
    }
  };

  const handleDeleteAlias = async (aliasId: number) => {
    if (confirm('Remove this alias?')) {
      try {
        await deleteAlias.mutateAsync(aliasId);
      } catch (error) {
        alert('Failed to delete alias');
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!symptom) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Symptom not found</p>
        <Button className="mt-4" onClick={() => router.push('/symptoms')}>
          Back to Symptoms
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{symptom.name_en}</h1>
              {symptom.is_global && (
                <Badge variant="outline">Global</Badge>
              )}
            </div>
            {symptom.name_bn && (
              <p className="text-gray-600 text-lg mt-1">{symptom.name_bn}</p>
            )}
          </div>
        </div>

        {!symptom.is_global && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/symptoms/${symptomId}/edit`)}
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
            <Button
              variant="outline"
              onClick={handleDelete}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Basic Information */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {symptom.category && (
            <div>
              <label className="text-sm font-medium text-gray-500">Category</label>
              <div className="mt-1">
                <Badge className={getCategoryColor(symptom.category)}>
                  {symptom.category.split('_').map(word =>
                    word.charAt(0).toUpperCase() + word.slice(1)
                  ).join(' ')}
                </Badge>
              </div>
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-500">Status</label>
            <div className="mt-1">
              <Badge variant={symptom.is_active ? 'default' : 'outline'}>
                {symptom.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      {/* Description */}
      {(symptom.description_en || symptom.description_bn) && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Description</h2>
          <div className="space-y-4">
            {symptom.description_en && (
              <div>
                <label className="text-sm font-medium text-gray-500">English</label>
                <p className="mt-1 text-gray-700">{symptom.description_en}</p>
              </div>
            )}
            {symptom.description_bn && (
              <div>
                <label className="text-sm font-medium text-gray-500">Bengali</label>
                <p className="mt-1 text-gray-700">{symptom.description_bn}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Aliases */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Aliases</h2>
          {!symptom.is_global && (
            <Button size="sm" onClick={() => setShowAddAlias(!showAddAlias)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Alias
            </Button>
          )}
        </div>

        {showAddAlias && !symptom.is_global && (
          <form onSubmit={handleAddAlias} className="mb-4 p-4 border rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Alias Name</label>
                <Input
                  value={aliasForm.alias_en}
                  onChange={(e) =>
                    setAliasForm({ ...aliasForm, alias_en: e.target.value })
                  }
                  placeholder="e.g., Cephalalgia, Migraine"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Type</label>
                <Select
                  value={aliasForm.alias_type}
                  onValueChange={(value) =>
                    setAliasForm({ ...aliasForm, alias_type: value as SymptomAliasType })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="medical">Medical Term</SelectItem>
                    <SelectItem value="colloquial">Colloquial</SelectItem>
                    <SelectItem value="regional">Regional Variation</SelectItem>
                    <SelectItem value="transliteration">Transliteration</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button type="submit" size="sm">Add</Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowAddAlias(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}

        {aliases.length > 0 ? (
          <div className="space-y-2">
            {aliases.map((alias) => (
              <div
                key={alias.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium">{alias.alias_en || alias.alias_bn}</span>
                  <Badge variant="outline" className="text-xs">
                    {alias.alias_type}
                  </Badge>
                </div>
                {!symptom.is_global && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteAlias(alias.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No aliases yet</p>
        )}
      </Card>
    </div>
  );
}
