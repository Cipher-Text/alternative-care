'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { MedicineAutocomplete } from '@/components/medicines/MedicineAutocomplete'
import type { PrescriptionItemCreate } from '@/types/prescription'
import type { MedicineSearchResult } from '@/types/medicine'
import { PlusCircle, Trash2, Edit2, Pill, Info } from 'lucide-react'

interface MedicineItemsBuilderProps {
  items: PrescriptionItemCreate[]
  onChange: (items: PrescriptionItemCreate[]) => void
  prescriptionId?: string
  isEdit?: boolean
}

interface MedicineFormData {
  medicine_name: string
  dosage: string
  frequency: string
  duration: string
  quantity: string
  instructions: string
}

const emptyFormData: MedicineFormData = {
  medicine_name: '',
  dosage: '',
  frequency: '',
  duration: '',
  quantity: '',
  instructions: '',
}

export function MedicineItemsBuilder({
  items,
  onChange,
  prescriptionId,
  isEdit = false,
}: MedicineItemsBuilderProps) {
  const t = useTranslations('rxItemsUi')
  const [showDialog, setShowDialog] = useState(false)
  const [editIndex, setEditIndex] = useState<number | null>(null)
  const [formData, setFormData] = useState<MedicineFormData>(emptyFormData)
  const [selectedMedicine, setSelectedMedicine] = useState<MedicineSearchResult | null>(null)
  const [useAutocomplete, setUseAutocomplete] = useState(true)

  const handleAddNew = () => {
    setEditIndex(null)
    setFormData(emptyFormData)
    setSelectedMedicine(null)
    setUseAutocomplete(true)
    setShowDialog(true)
  }

  const handleEdit = (index: number) => {
    const item = items[index]
    setEditIndex(index)
    setFormData({
      medicine_name: item.medicine_name || '',
      dosage: item.dosage,
      frequency: item.frequency,
      duration: item.duration || '',
      quantity: item.quantity?.toString() || '',
      instructions: item.instructions || '',
    })
    setSelectedMedicine(null)
    setUseAutocomplete(false)
    setShowDialog(true)
  }

  const handleMedicineSelect = (medicine: MedicineSearchResult) => {
    setSelectedMedicine(medicine)
    setFormData({
      ...formData,
      medicine_name: medicine.potency
        ? `${medicine.name_en} ${medicine.potency}`
        : medicine.name_en,
      dosage: medicine.dosage_guidance_en || formData.dosage,
    })
  }

  const handleDelete = (index: number) => {
    const newItems = items.filter((_, i) => i !== index)
    onChange(newItems)
  }

  const handleSave = () => {
    if (!formData.medicine_name || !formData.dosage || !formData.frequency) {
      return
    }

    const newItem: PrescriptionItemCreate = {
      medicine_name: formData.medicine_name,
      dosage: formData.dosage,
      frequency: formData.frequency,
      duration: formData.duration || null,
      quantity: formData.quantity ? parseInt(formData.quantity) : null,
      instructions: formData.instructions || null,
      display_order: editIndex !== null ? items[editIndex].display_order : items.length,
    }

    if (editIndex !== null) {
      // Edit existing
      const newItems = [...items]
      newItems[editIndex] = newItem
      onChange(newItems)
    } else {
      // Add new
      onChange([...items, newItem])
    }

    setShowDialog(false)
    setFormData(emptyFormData)
    setEditIndex(null)
  }

  const isFormValid = formData.medicine_name && formData.dosage && formData.frequency

  return (
    <div className="space-y-4">
      {items.length > 0 ? (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>{t('colMedicine')}</TableHead>
                <TableHead>{t('colDosage')}</TableHead>
                <TableHead>{t('colFrequency')}</TableHead>
                <TableHead>{t('colDuration')}</TableHead>
                <TableHead>{t('colQty')}</TableHead>
                <TableHead>{t('colInstructions')}</TableHead>
                <TableHead className="w-24 text-right">{t('colActions')}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{index + 1}</TableCell>
                  <TableCell className="font-medium">
                    {item.medicine_name || t('medicineIdFallback', { id: String(item.medicine_id) })}
                  </TableCell>
                  <TableCell>{item.dosage}</TableCell>
                  <TableCell>{item.frequency}</TableCell>
                  <TableCell>{item.duration || '-'}</TableCell>
                  <TableCell>{item.quantity || '-'}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {item.instructions || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label={t('editAria')}
                        onClick={() => handleEdit(index)}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label={t('deleteAria')}
                        onClick={() => handleDelete(index)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <Card className="p-8 text-center">
          <Pill className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground mb-4">{t('noMedicines')}</p>
          <Button onClick={handleAddNew} variant="outline">
            <PlusCircle className="mr-2 h-4 w-4" />
            {t('addFirst')}
          </Button>
        </Card>
      )}

      {items.length > 0 && (
        <Button onClick={handleAddNew} variant="outline" className="w-full">
          <PlusCircle className="mr-2 h-4 w-4" />
          {t('addMedicine')}
        </Button>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editIndex !== null ? t('editMedicine') : t('addMedicine')}
            </DialogTitle>
            <DialogDescription>
              {editIndex !== null
                ? t('updateDesc')
                : t('enterDesc')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Medicine Name */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <Label htmlFor="medicine_name">
                  {t('medicineName')} <span className="text-red-500">*</span>
                </Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setUseAutocomplete(!useAutocomplete)}
                  className="text-xs"
                >
                  {useAutocomplete ? t('useFreeText') : t('searchDatabase')}
                </Button>
              </div>

              {useAutocomplete ? (
                <>
                  <MedicineAutocomplete
                    onSelect={handleMedicineSelect}
                    placeholder={t('autocompletePlaceholder')}
                    defaultValue={formData.medicine_name}
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('autocompleteHint')}
                  </p>
                </>
              ) : (
                <>
                  <Input
                    id="medicine_name"
                    placeholder={t('namePlaceholder')}
                    value={formData.medicine_name}
                    onChange={(e) =>
                      setFormData({ ...formData, medicine_name: e.target.value })
                    }
                    autoFocus
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('nameHint')}
                  </p>
                </>
              )}

              {/* Show selected medicine details */}
              {selectedMedicine && (
                <Card className="p-3 bg-blue-50 border-blue-200">
                  <div className="flex items-start gap-3">
                    <Info className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium">{selectedMedicine.name_en}</span>
                        {selectedMedicine.potency && (
                          <Badge variant="outline" className="text-xs">
                            {selectedMedicine.potency}
                          </Badge>
                        )}
                      </div>
                      {selectedMedicine.dosage_guidance_en && (
                        <p className="text-xs text-gray-700">
                          <span className="font-medium">{t('suggestedDosage')}</span>
                          {selectedMedicine.dosage_guidance_en}
                        </p>
                      )}
                      {selectedMedicine.indications_en && (
                        <p className="text-xs text-gray-600 mt-1">
                          <span className="font-medium">{t('usedFor')}</span>
                          {selectedMedicine.indications_en.slice(0, 150)}
                          {selectedMedicine.indications_en.length > 150 ? '...' : ''}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              )}
            </div>

            {/* Dosage and Frequency */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dosage">
                  {t('dosage')} <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="dosage"
                  placeholder={t('dosagePlaceholder')}
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency">
                  {t('frequency')} <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="frequency"
                  placeholder={t('frequencyPlaceholder')}
                  value={formData.frequency}
                  onChange={(e) =>
                    setFormData({ ...formData, frequency: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Duration and Quantity */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="duration">{t('durationOptional')}</Label>
                <Input
                  id="duration"
                  placeholder={t('durationPlaceholder')}
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="quantity">{t('quantityOptional')}</Label>
                <Input
                  id="quantity"
                  type="number"
                  placeholder={t('quantityPlaceholder')}
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
            </div>

            {/* Instructions */}
            <div className="space-y-2">
              <Label htmlFor="instructions">{t('instructionsOptional')}</Label>
              <Textarea
                id="instructions"
                placeholder={t('instructionsPlaceholder')}
                value={formData.instructions}
                onChange={(e) =>
                  setFormData({ ...formData, instructions: e.target.value })
                }
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              {t('cancel')}
            </Button>
            <Button onClick={handleSave} disabled={!isFormValid}>
              {editIndex !== null ? t('updateMedicine') : t('addMedicineBtn')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
