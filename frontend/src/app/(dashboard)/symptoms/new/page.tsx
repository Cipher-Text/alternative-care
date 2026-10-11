/**
 * Create New Symptom Page
 */

'use client';

import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateSymptom } from '@/lib/hooks/useSymptoms';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { ArrowLeft, Save } from 'lucide-react';
import type { SymptomCategory } from '@/types/symptom';

export default function NewSymptomPage() {
  const router = useRouter();
  const t = useTranslations('symptomFormUi');
  const tc = useTranslations('symptomCategoryUi');
  const createSymptom = useCreateSymptom();

  const [formData, setFormData] = useState({
    name_en: '',
    name_bn: '',
    category: '' as SymptomCategory,
    description_en: '',
    description_bn: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name_en.trim()) {
      newErrors.name_en = t('nameRequired');
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

      await createSymptom.mutateAsync(payload as any);
      router.push('/symptoms');
    } catch (error) {
      alert(t('createFailed'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('back')}
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{t('addTitle')}</h1>
          <p className="text-gray-600 mt-2">{t('addSubtitle')}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="p-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('basicInfo')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('nameEn')} <span className="text-red-500">*</span>
                  </label>
                  <Input
                    value={formData.name_en}
                    onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                    placeholder={t('nameEnPlaceholder')}
                  />
                  {errors.name_en && (
                    <p className="text-red-500 text-sm mt-1">{errors.name_en}</p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('nameBn')}</label>
                  <Input
                    value={formData.name_bn}
                    onChange={(e) => setFormData({ ...formData, name_bn: e.target.value })}
                    placeholder={t('nameBnPlaceholder')}
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="text-sm font-medium mb-2 block">{t('category')}</label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) =>
                      setFormData({ ...formData, category: value as SymptomCategory })
                    }
                  >
                    <SelectTrigger aria-label={t('category')}>
                      <SelectValue placeholder={t('categoryPlaceholder')} />
                    </SelectTrigger>
                    <SelectContent>
                      {['neurological','respiratory','digestive','mental','musculoskeletal','skin','immune','cardiovascular','metabolic','reproductive','ear_nose_throat','urinary'].map((c) => (
                        <SelectItem key={c} value={c}>{tc(c)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* Description */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('description')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">{t('descEn')}</label>
                  <Textarea
                    value={formData.description_en}
                    onChange={(e) => setFormData({ ...formData, description_en: e.target.value })}
                    placeholder={t('descEnPlaceholder')}
                    rows={6}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('descBn')}</label>
                  <Textarea
                    value={formData.description_bn}
                    onChange={(e) => setFormData({ ...formData, description_bn: e.target.value })}
                    placeholder={t('descBnPlaceholder')}
                    rows={6}
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={createSymptom.isLoading}>
                {createSymptom.isLoading ? (
                  <>{t('creating')}</>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {t('create')}
                  </>
                )}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                {t('cancel')}
              </Button>
            </div>
          </div>
        </Card>
      </form>
    </div>
  );
}
