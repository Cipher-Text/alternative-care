/**
 * Medicine Detail Page
 */

'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMedicine, useMedicineAliases, useDeleteMedicine, useCreateMedicineAlias, useDeleteMedicineAlias } from '@/lib/hooks/useMedicines';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, ArrowLeft, Edit, Trash2, Plus, X } from 'lucide-react';
import type { MedicalSystem, MedicineAliasType } from '@/types/medicine';

export default function MedicineDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const medicineId = parseInt(id);

  const { data: medicine, isLoading } = useMedicine(medicineId);
  const { data: aliases = [] } = useMedicineAliases(medicineId);
  const deleteMedicine = useDeleteMedicine();
  const createAlias = useCreateMedicineAlias();
  const deleteAlias = useDeleteMedicineAlias();

  const [showAddAlias, setShowAddAlias] = useState(false);
  const [aliasForm, setAliasForm] = useState({
    alias_name: '',
    alias_type: '' as MedicineAliasType,
  });

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this medicine?')) {
      try {
        await deleteMedicine.mutateAsync(medicineId);
        router.push('/medicines');
      } catch (error) {
        alert('Failed to delete medicine');
      }
    }
  };

  const handleAddAlias = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aliasForm.alias_name.trim() || !aliasForm.alias_type) return;

    try {
      await createAlias.mutateAsync({
        medicineId,
        payload: aliasForm,
      });
      setAliasForm({ alias_name: '', alias_type: '' as MedicineAliasType });
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!medicine) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Medicine not found</p>
        <Button className="mt-4" onClick={() => router.push('/medicines')}>
          Back to Medicines
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
              <h1 className="text-3xl font-bold">{medicine.name_en}</h1>
              {medicine.is_global && (
                <Badge variant="outline">Global</Badge>
              )}
            </div>
            {medicine.name_bn && (
              <p className="text-gray-600 text-lg mt-1">{medicine.name_bn}</p>
            )}
          </div>
        </div>

        {!medicine.is_global && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/medicines/${medicineId}/edit`)}
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
          <div>
            <label className="text-sm font-medium text-gray-500">Medical System</label>
            <div className="mt-1">
              <Badge className={getSystemColor(medicine.system)}>
                {medicine.system.charAt(0).toUpperCase() + medicine.system.slice(1)}
              </Badge>
            </div>
          </div>

          {medicine.category && (
            <div>
              <label className="text-sm font-medium text-gray-500">Category</label>
              <p className="mt-1">{medicine.category}</p>
            </div>
          )}

          {medicine.potency && (
            <div>
              <label className="text-sm font-medium text-gray-500">Potency</label>
              <p className="mt-1">{medicine.potency}</p>
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-500">Status</label>
            <div className="mt-1">
              <Badge variant={medicine.is_active ? 'default' : 'outline'}>
                {medicine.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      {/* Description */}
      {(medicine.description_en || medicine.description_bn) && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Description</h2>
          <div className="space-y-4">
            {medicine.description_en && (
              <div>
                <label className="text-sm font-medium text-gray-500">English</label>
                <p className="mt-1 text-gray-700">{medicine.description_en}</p>
              </div>
            )}
            {medicine.description_bn && (
              <div>
                <label className="text-sm font-medium text-gray-500">Bengali</label>
                <p className="mt-1 text-gray-700">{medicine.description_bn}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Dosage Guidance */}
      {(medicine.dosage_guidance_en || medicine.dosage_guidance_bn) && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Dosage Guidance</h2>
          <div className="space-y-4">
            {medicine.dosage_guidance_en && (
              <div>
                <label className="text-sm font-medium text-gray-500">English</label>
                <p className="mt-1 text-gray-700">{medicine.dosage_guidance_en}</p>
              </div>
            )}
            {medicine.dosage_guidance_bn && (
              <div>
                <label className="text-sm font-medium text-gray-500">Bengali</label>
                <p className="mt-1 text-gray-700">{medicine.dosage_guidance_bn}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Indications */}
      {(medicine.indications_en || medicine.indications_bn) && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Indications</h2>
          <div className="space-y-4">
            {medicine.indications_en && (
              <div>
                <label className="text-sm font-medium text-gray-500">English</label>
                <p className="mt-1 text-gray-700">{medicine.indications_en}</p>
              </div>
            )}
            {medicine.indications_bn && (
              <div>
                <label className="text-sm font-medium text-gray-500">Bengali</label>
                <p className="mt-1 text-gray-700">{medicine.indications_bn}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Contraindications */}
      {(medicine.contraindications_en || medicine.contraindications_bn) && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Contraindications</h2>
          <div className="space-y-4">
            {medicine.contraindications_en && (
              <div>
                <label className="text-sm font-medium text-gray-500">English</label>
                <p className="mt-1 text-gray-700">{medicine.contraindications_en}</p>
              </div>
            )}
            {medicine.contraindications_bn && (
              <div>
                <label className="text-sm font-medium text-gray-500">Bengali</label>
                <p className="mt-1 text-gray-700">{medicine.contraindications_bn}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Aliases */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Aliases</h2>
          {!medicine.is_global && (
            <Button size="sm" onClick={() => setShowAddAlias(!showAddAlias)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Alias
            </Button>
          )}
        </div>

        {showAddAlias && !medicine.is_global && (
          <form onSubmit={handleAddAlias} className="mb-4 p-4 border rounded-lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Alias Name</label>
                <Input
                  value={aliasForm.alias_name}
                  onChange={(e) =>
                    setAliasForm({ ...aliasForm, alias_name: e.target.value })
                  }
                  placeholder="e.g., Arnica, Mountain Daisy"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Type</label>
                <Select
                  value={aliasForm.alias_type}
                  onValueChange={(value) =>
                    setAliasForm({ ...aliasForm, alias_type: value as MedicineAliasType })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="brand">Brand Name</SelectItem>
                    <SelectItem value="common">Common Name</SelectItem>
                    <SelectItem value="transliteration">Transliteration</SelectItem>
                    <SelectItem value="abbreviation">Abbreviation</SelectItem>
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
                  <span className="font-medium">{alias.alias_name}</span>
                  <Badge variant="outline" className="text-xs">
                    {alias.alias_type}
                  </Badge>
                </div>
                {!medicine.is_global && (
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
