/**
 * Edit Medicine Page
 */

'use client';

import { use, useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useMedicine, useUpdateMedicine } from '@/lib/hooks/useMedicines';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, ArrowLeft, Save } from 'lucide-react';
import type { MedicalSystem, MedicineUpdate } from '@/types/medicine';

export default function EditMedicinePage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const t = useTranslations('libFormUi');
  const ts = useTranslations('libSystemUi');
  const { id } = use(params);
  const medicineId = parseInt(id);

  const { data: medicine, isLoading } = useMedicine(medicineId);
  const updateMedicine = useUpdateMedicine();

  const [formData, setFormData] = useState({
    name_en: '',
    name_bn: '',
    system: '' as MedicalSystem,
    category: '',
    potency: '',
    description_en: '',
    description_bn: '',
    dosage_guidance_en: '',
    dosage_guidance_bn: '',
    indications_en: '',
    indications_bn: '',
    contraindications_en: '',
    contraindications_bn: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (medicine) {
      setFormData({
        name_en: medicine.name_en,
        name_bn: medicine.name_bn || '',
        system: medicine.system,
        category: medicine.category || '',
        potency: medicine.potency || '',
        description_en: medicine.description_en || '',
        description_bn: medicine.description_bn || '',
        dosage_guidance_en: medicine.dosage_guidance_en || '',
        dosage_guidance_bn: medicine.dosage_guidance_bn || '',
        indications_en: medicine.indications_en || '',
        indications_bn: medicine.indications_bn || '',
        contraindications_en: medicine.contraindications_en || '',
        contraindications_bn: medicine.contraindications_bn || '',
      });
    }
  }, [medicine]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name_en.trim()) {
      newErrors.name_en = t('nameRequired');
    }
    if (!formData.system) {
      newErrors.system = t('systemRequired');
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
        potency: formData.potency || undefined,
        description_en: formData.description_en || undefined,
        description_bn: formData.description_bn || undefined,
        dosage_guidance_en: formData.dosage_guidance_en || undefined,
        dosage_guidance_bn: formData.dosage_guidance_bn || undefined,
        indications_en: formData.indications_en || undefined,
        indications_bn: formData.indications_bn || undefined,
        contraindications_en: formData.contraindications_en || undefined,
        contraindications_bn: formData.contraindications_bn || undefined,
      };

      await updateMedicine.mutateAsync({ id: medicineId, data: payload as MedicineUpdate });
      router.push(`/medicines/${medicineId}`);
    } catch (error) {
      alert(t('updateFailed'));
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
        <p className="text-gray-500">{t('notFound')}</p>
        <Button className="mt-4" onClick={() => router.push('/medicines')}>
          {t('backToMedicines')}
        </Button>
      </div>
    );
  }

  if (medicine.is_global) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{t('globalNoEdit')}</p>
        <Button className="mt-4" onClick={() => router.push(`/medicines/${medicineId}`)}>
          {t('backToMedicine')}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('back')}
        </Button>
        <div>
          <h1 className="text-3xl font-bold">{t('editTitle')}</h1>
          <p className="text-gray-600 mt-2">{medicine.name_en}</p>
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
                    placeholder={t('nameEnPh')}
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
                    placeholder={t('nameBnPh')}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('medicalSystem')} <span className="text-red-500">*</span>
                  </label>
                  <Select
                    value={formData.system}
                    onValueChange={(value) =>
                      setFormData({ ...formData, system: value as MedicalSystem })
                    }
                  >
                    <SelectTrigger aria-label={t('medicalSystem')}>
                      <SelectValue placeholder={t('selectSystem')} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="homeopathy">{ts('homeopathy')}</SelectItem>
                      <SelectItem value="ayurveda">{ts('ayurveda')}</SelectItem>
                      <SelectItem value="unani">{ts('unani')}</SelectItem>
                      <SelectItem value="herbal">{ts('herbal')}</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.system && (
                    <p className="text-red-500 text-sm mt-1">{errors.system}</p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('category')}</label>
                  <Input
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder={t('categoryPh')}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('potency')}
                    {formData.system === 'homeopathy' && (
                      <span className="text-gray-500 text-xs ml-2">{t('potencyHint')}</span>
                    )}
                  </label>
                  <Input
                    value={formData.potency}
                    onChange={(e) => setFormData({ ...formData, potency: e.target.value })}
                    placeholder={formData.system === 'homeopathy' ? '30C' : t('optional')}
                  />
                </div>
              </div>
            </div>

            {/* Description */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('description')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">{t('descriptionEn')}</label>
                  <Textarea
                    value={formData.description_en}
                    onChange={(e) => setFormData({ ...formData, description_en: e.target.value })}
                    placeholder={t('descriptionEnPh')}
                    rows={4}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('descriptionBn')}</label>
                  <Textarea
                    value={formData.description_bn}
                    onChange={(e) => setFormData({ ...formData, description_bn: e.target.value })}
                    placeholder={t('descriptionBnPh')}
                    rows={4}
                  />
                </div>
              </div>
            </div>

            {/* Dosage Guidance */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('dosageGuidance')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">{t('dosageEn')}</label>
                  <Textarea
                    value={formData.dosage_guidance_en}
                    onChange={(e) =>
                      setFormData({ ...formData, dosage_guidance_en: e.target.value })
                    }
                    placeholder={t('dosageEnPh')}
                    rows={3}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('dosageBn')}</label>
                  <Textarea
                    value={formData.dosage_guidance_bn}
                    onChange={(e) =>
                      setFormData({ ...formData, dosage_guidance_bn: e.target.value })
                    }
                    placeholder={t('dosageBnPh')}
                    rows={3}
                  />
                </div>
              </div>
            </div>

            {/* Indications */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('indications')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">{t('indicationsEn')}</label>
                  <Textarea
                    value={formData.indications_en}
                    onChange={(e) => setFormData({ ...formData, indications_en: e.target.value })}
                    placeholder={t('indicationsEnPh')}
                    rows={4}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">{t('indicationsBn')}</label>
                  <Textarea
                    value={formData.indications_bn}
                    onChange={(e) => setFormData({ ...formData, indications_bn: e.target.value })}
                    placeholder={t('indicationsBnPh')}
                    rows={4}
                  />
                </div>
              </div>
            </div>

            {/* Contraindications */}
            <div>
              <h3 className="text-lg font-semibold mb-4">{t('contraindications')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('contraindicationsEn')}
                  </label>
                  <Textarea
                    value={formData.contraindications_en}
                    onChange={(e) =>
                      setFormData({ ...formData, contraindications_en: e.target.value })
                    }
                    placeholder={t('contraindicationsEnPh')}
                    rows={4}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    {t('contraindicationsBn')}
                  </label>
                  <Textarea
                    value={formData.contraindications_bn}
                    onChange={(e) =>
                      setFormData({ ...formData, contraindications_bn: e.target.value })
                    }
                    placeholder={t('contraindicationsBnPh')}
                    rows={4}
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Button type="submit" disabled={updateMedicine.isLoading}>
                {updateMedicine.isLoading ? (
                  <>{t('saving')}</>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {t('saveChanges')}
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
