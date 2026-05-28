/**
 * Edit Symptom Page
 */

'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSymptom, useUpdateSymptom } from '@/lib/hooks/useSymptoms';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, ArrowLeft, Save } from 'lucide-react';
import type { SymptomCategory } from '@/types/symptom';

export default function EditSymptomPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const symptomId = parseInt(id);

  const { data: symptom, isLoading } = useSymptom(symptomId);
  const updateSymptom = useUpdateSymptom();

  const [formData, setFormData] = useState({
    name_en: '',
    name_bn: '',
    category: '' as SymptomCategory,
    description_en: '',
    description_bn: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (symptom) {
      setFormData({
        name_en: symptom.name_en,
        name_bn: symptom.name_bn || '',
        category: symptom.category || ('' as SymptomCategory),
        description_en: symptom.description_en || '',
        description_bn: symptom.description_bn || '',
      });
    }
  }, [symptom]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name_en.trim()) {
      newErrors.name_en = 'English name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const payload = {
        ...formData,
        name_bn: formData.name_bn || undefined,
        category: formData.category || undefined,
        description_en: formData.description_en || undefined,
        description_bn: formData.description_bn || undefined,
      };

      await updateSymptom.mutateAsync({ id: symptomId, payload: payload as any });
      router.push(`/symptoms/${symptomId}`);
    } catch (error) {
      alert('Failed to update symptom');
    }
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

  if (symptom.is_global) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Global symptoms cannot be edited</p>
        <Button className="mt-4" onClick={() => router.push(`/symptoms/${symptomId}`)}>
          Back to Symptom
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Edit Symptom</h1>
          <p className="text-gray-600 mt-2">{symptom.name_en}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="p-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Name (English) <span className="text-red-500">*</span>
                  </label>
                  <Input
                    value={formData.name_en}
                    onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                    placeholder="e.g., Headache"
                  />
                  {errors.name_en && (
                    <p className="text-red-500 text-sm mt-1">{errors.name_en}</p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Name (Bengali)</label>
                  <Input
                    value={formData.name_bn}
                    onChange={(e) => setFormData({ ...formData, name_bn: e.target.value })}
                    placeholder="e.g., মাথাব্যথা"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="text-sm font-medium mb-2 block">Category</label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) =>
                      setFormData({ ...formData, category: value as SymptomCategory })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category (optional)" />
                    </SelectTrigger>
                    <SelectContent>
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
              </div>
            </div>

            {/* Description */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Description</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Description (English)</label>
                  <Textarea
                    value={formData.description_en}
                    onChange={(e) => setFormData({ ...formData, description_en: e.target.value })}
                    placeholder="Describe the symptom..."
                    rows={6}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Description (Bengali)</label>
                  <Textarea
                    value={formData.description_bn}
                    onChange={(e) => setFormData({ ...formData, description_bn: e.target.value })}
                    placeholder="লক্ষণের বর্ণনা..."
                    rows={6}
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={updateSymptom.isLoading}>
                {updateSymptom.isLoading ? (
                  <>Saving...</>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
