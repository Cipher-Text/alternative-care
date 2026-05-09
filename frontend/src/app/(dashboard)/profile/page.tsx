'use client'

import { useState } from 'react'
import { useDoctorProfile } from '@/lib/hooks/useDoctor'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ProfileForm } from '@/components/doctor/ProfileForm'
import { DegreesSection } from '@/components/doctor/DegreesSection'
import { TrainingsSection } from '@/components/doctor/TrainingsSection'
import {
  User,
  Building2,
  GraduationCap,
  Award,
  Loader2,
  AlertCircle,
  CheckCircle,
  Edit,
} from 'lucide-react'

type Tab = 'profile' | 'degrees' | 'trainings'

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const { data: profile, isLoading, error } = useDoctorProfile()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">Failed to Load Profile</h2>
        <p className="text-muted-foreground mb-4">
          There was an error loading your profile. Please try again.
        </p>
      </div>
    )
  }

  const tabs = [
    { id: 'profile' as Tab, label: 'Profile', icon: User },
    { id: 'degrees' as Tab, label: 'Degrees', icon: GraduationCap },
    { id: 'trainings' as Tab, label: 'Trainings', icon: Award },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Doctor Profile</h1>
          <p className="text-muted-foreground">Manage your professional information</p>
        </div>
        <div className="flex items-center gap-3">
          {profile.is_verified ? (
            <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              <CheckCircle className="h-3 w-3 mr-1" />
              Verified
            </Badge>
          ) : (
            <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
              <AlertCircle className="h-3 w-3 mr-1" />
              Pending Verification
            </Badge>
          )}
          <Badge variant="outline" className="capitalize">
            {profile.plan} Plan
          </Badge>
        </div>
      </div>

      {/* Profile Summary Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-6">
            <div className="bg-indigo-100 dark:bg-indigo-900 p-4 rounded-full">
              <User className="h-12 w-12 text-indigo-600 dark:text-indigo-300" />
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold">{profile.full_name}</h2>
              <p className="text-muted-foreground">{profile.email}</p>
              {profile.phone && <p className="text-sm text-muted-foreground">{profile.phone}</p>}
              <div className="mt-4 flex flex-wrap gap-2">
                {profile.specializations.map((spec) => (
                  <Badge key={spec} variant="outline" className="capitalize">
                    {spec}
                  </Badge>
                ))}
              </div>
            </div>
            {activeTab === 'profile' && !isEditingProfile && (
              <Button onClick={() => setIsEditingProfile(true)} variant="outline">
                <Edit className="h-4 w-4 mr-2" />
                Edit Profile
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id)
                  if (tab.id !== 'profile') setIsEditingProfile(false)
                }}
                className={`flex items-center gap-2 pb-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600 font-medium'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'profile' && (
        <ProfileForm
          profile={profile}
          isEditing={isEditingProfile}
          onCancel={() => setIsEditingProfile(false)}
          onSuccess={() => setIsEditingProfile(false)}
        />
      )}

      {activeTab === 'degrees' && <DegreesSection />}

      {activeTab === 'trainings' && <TrainingsSection />}
    </div>
  )
}
