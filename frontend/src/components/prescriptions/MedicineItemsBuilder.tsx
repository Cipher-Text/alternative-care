'use client'

import { useState } from 'react'
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
import type { PrescriptionItemCreate } from '@/types/prescription'
import { PlusCircle, Trash2, Edit2, Pill } from 'lucide-react'

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
  const [showDialog, setShowDialog] = useState(false)
  const [editIndex, setEditIndex] = useState<number | null>(null)
  const [formData, setFormData] = useState<MedicineFormData>(emptyFormData)

  const handleAddNew = () => {
    setEditIndex(null)
    setFormData(emptyFormData)
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
    setShowDialog(true)
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
                <TableHead>Medicine</TableHead>
                <TableHead>Dosage</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Qty</TableHead>
                <TableHead>Instructions</TableHead>
                <TableHead className="w-24 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{index + 1}</TableCell>
                  <TableCell className="font-medium">
                    {item.medicine_name || `Medicine ID: ${item.medicine_id}`}
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
                        onClick={() => handleEdit(index)}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
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
          <p className="text-muted-foreground mb-4">No medicines added yet</p>
          <Button onClick={handleAddNew} variant="outline">
            <PlusCircle className="mr-2 h-4 w-4" />
            Add First Medicine
          </Button>
        </Card>
      )}

      {items.length > 0 && (
        <Button onClick={handleAddNew} variant="outline" className="w-full">
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Medicine
        </Button>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editIndex !== null ? 'Edit Medicine' : 'Add Medicine'}
            </DialogTitle>
            <DialogDescription>
              {editIndex !== null
                ? 'Update the medicine details below'
                : 'Enter the medicine details below'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Medicine Name */}
            <div className="space-y-2">
              <Label htmlFor="medicine_name">
                Medicine Name <span className="text-red-500">*</span>
              </Label>
              <Input
                id="medicine_name"
                placeholder="e.g., Arnica Montana, Nux Vomica"
                value={formData.medicine_name}
                onChange={(e) =>
                  setFormData({ ...formData, medicine_name: e.target.value })
                }
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Enter the full medicine name including potency if applicable
              </p>
            </div>

            {/* Dosage and Frequency */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dosage">
                  Dosage <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="dosage"
                  placeholder="e.g., 2 drops, 5 pills"
                  value={formData.dosage}
                  onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="frequency">
                  Frequency <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="frequency"
                  placeholder="e.g., 3 times daily, Every 4 hours"
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
                <Label htmlFor="duration">Duration (Optional)</Label>
                <Input
                  id="duration"
                  placeholder="e.g., 7 days, 2 weeks"
                  value={formData.duration}
                  onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="quantity">Quantity (Optional)</Label>
                <Input
                  id="quantity"
                  type="number"
                  placeholder="e.g., 30"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                />
              </div>
            </div>

            {/* Instructions */}
            <div className="space-y-2">
              <Label htmlFor="instructions">Instructions (Optional)</Label>
              <Textarea
                id="instructions"
                placeholder="e.g., Take before meals, Avoid spicy food while taking this medicine"
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
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!isFormValid}>
              {editIndex !== null ? 'Update' : 'Add'} Medicine
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
