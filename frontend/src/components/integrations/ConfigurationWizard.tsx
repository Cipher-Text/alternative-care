/**
 * Configuration Wizard Component
 * Step-by-step wizard for setting up integrations
 */

'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  useProvider,
  useCreateIntegration,
  useUpdateIntegration,
  useTestIntegration,
} from '@/lib/hooks/useIntegrations';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import type {
  TenantIntegrationCreate,
  TenantIntegrationUpdate,
  ConfigSchemaField,
} from '@/types/integration';

interface ConfigurationWizardProps {
  providerId: number | null;
  integrationId?: number | null;
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type WizardStep = 'configure' | 'test' | 'complete';

export function ConfigurationWizard({
  providerId,
  integrationId,
  open,
  onClose,
  onSuccess,
}: ConfigurationWizardProps) {
  const [step, setStep] = useState<WizardStep>('configure');
  const [createdIntegrationId, setCreatedIntegrationId] = useState<number | null>(null);

  const { data: provider, isLoading: loadingProvider } = useProvider(providerId || 0);
  const createIntegration = useCreateIntegration();
  const updateIntegration = useUpdateIntegration();
  const testIntegration = useTestIntegration();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
  } = useForm();

  const onSubmit = async (formData: any) => {
    if (!provider) return;

    try {
      // Extract credentials and display name
      const { display_name, test_phone, test_email, ...credentials } = formData;

      const payload: TenantIntegrationCreate | TenantIntegrationUpdate = {
        provider_id: provider.id,
        display_name: display_name || provider.display_name,
        credentials,
        is_active: true,
      };

      let integrationIdToTest: number;

      if (integrationId) {
        // Update existing integration
        const result = await updateIntegration.mutateAsync({
          integrationId,
          payload: payload as TenantIntegrationUpdate,
        });
        integrationIdToTest = result.id;
      } else {
        // Create new integration
        const result = await createIntegration.mutateAsync(
          payload as TenantIntegrationCreate
        );
        integrationIdToTest = result.id;
        setCreatedIntegrationId(result.id);
      }

      // Move to test step
      setStep('test');

      // Auto-test if test credentials provided
      if (test_phone || test_email) {
        await testIntegration.mutateAsync({
          integrationId: integrationIdToTest,
          payload: {
            test_phone,
            test_email,
          },
        });
      }
    } catch (error) {
      console.error('Failed to configure integration:', error);
    }
  };

  const handleTest = async () => {
    const testData = watch();
    const integrationIdToTest = integrationId || createdIntegrationId;

    if (!integrationIdToTest || !provider) return;

    try {
      await testIntegration.mutateAsync({
        integrationId: integrationIdToTest,
        payload: {
          test_phone: testData.test_phone,
          test_email: testData.test_email,
        },
      });
      setStep('complete');
    } catch (error) {
      console.error('Test failed:', error);
    }
  };

  const handleComplete = () => {
    onSuccess?.();
    onClose();
    // Reset state
    setStep('configure');
    setCreatedIntegrationId(null);
  };

  if (!open || !providerId) return null;

  if (loadingProvider) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!provider) {
    return (
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent>
          <div className="text-center py-12">
            <p className="text-gray-500">Provider not found</p>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            {provider.logo_url && (
              <img
                src={provider.logo_url}
                alt={provider.display_name}
                className="w-10 h-10 object-contain"
              />
            )}
            <div>
              <DialogTitle>
                {integrationId ? 'Update' : 'Setup'} {provider.display_name}
              </DialogTitle>
              <Badge className="mt-1">{provider.provider_type.toUpperCase()}</Badge>
            </div>
          </div>
          {provider.description && (
            <p className="text-sm text-gray-600 mt-2">{provider.description}</p>
          )}
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {step === 'configure' && (
            <>
              {/* Display Name */}
              <div>
                <Label htmlFor="display_name">Display Name (Optional)</Label>
                <Input
                  id="display_name"
                  {...register('display_name')}
                  placeholder={`e.g., ${provider.display_name} - Production`}
                />
              </div>

              {/* Dynamic Credential Fields */}
              {provider.config_schema &&
                Object.entries(provider.config_schema).map(([key, field]: [string, any]) => {
                  const fieldSchema = field as ConfigSchemaField;
                  return (
                    <div key={key}>
                      <Label htmlFor={key}>
                        {fieldSchema.label}
                        {fieldSchema.required && <span className="text-red-500">*</span>}
                      </Label>
                      <Input
                        id={key}
                        type={fieldSchema.sensitive ? 'password' : 'text'}
                        {...register(key, {
                          required: fieldSchema.required
                            ? `${fieldSchema.label} is required`
                            : false,
                        })}
                        placeholder={fieldSchema.description}
                      />
                      {errors[key] && (
                        <p className="text-sm text-red-500 mt-1">
                          {errors[key]?.message as string}
                        </p>
                      )}
                      {fieldSchema.description && (
                        <p className="text-xs text-gray-500 mt-1">
                          {fieldSchema.description}
                        </p>
                      )}
                    </div>
                  );
                })}

              {/* Test Credentials */}
              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Test Configuration (Optional)</h3>
                {provider.provider_type === 'sms' && (
                  <div>
                    <Label htmlFor="test_phone">Test Phone Number</Label>
                    <Input
                      id="test_phone"
                      {...register('test_phone')}
                      placeholder="e.g., +8801712345678"
                    />
                  </div>
                )}
                {provider.provider_type === 'email' && (
                  <div>
                    <Label htmlFor="test_email">Test Email Address</Label>
                    <Input
                      id="test_email"
                      type="email"
                      {...register('test_email')}
                      placeholder="e.g., test@example.com"
                    />
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  {integrationId ? 'Update' : 'Create'} Integration
                </Button>
              </div>
            </>
          )}

          {step === 'test' && (
            <div className="space-y-4">
              {testIntegration.isLoading ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-500 mb-4" />
                  <p className="text-gray-600">Testing connection...</p>
                </div>
              ) : testIntegration.data ? (
                <div className="space-y-4">
                  <div
                    className={`flex items-start gap-3 p-4 rounded-lg ${
                      testIntegration.data.success
                        ? 'bg-green-50 border border-green-200'
                        : 'bg-red-50 border border-red-200'
                    }`}
                  >
                    {testIntegration.data.success ? (
                      <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium">
                        {testIntegration.data.success ? 'Test Successful!' : 'Test Failed'}
                      </p>
                      <p className="text-sm mt-1">{testIntegration.data.message}</p>
                      {testIntegration.data.error && (
                        <p className="text-sm text-red-600 mt-2">
                          Error: {testIntegration.data.error}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setStep('configure')}
                    >
                      Back to Configuration
                    </Button>
                    {testIntegration.data.success ? (
                      <Button type="button" onClick={() => setStep('complete')}>
                        Continue
                      </Button>
                    ) : (
                      <Button type="button" onClick={handleTest}>
                        Retry Test
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-50 border border-blue-200">
                    <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0" />
                    <div>
                      <p className="font-medium">Ready to Test</p>
                      <p className="text-sm mt-1">
                        Click the button below to test your integration configuration.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setStep('configure')}
                    >
                      Back to Configuration
                    </Button>
                    <Button type="button" onClick={handleTest}>
                      Test Connection
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setStep('complete')}>
                      Skip Test
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {step === 'complete' && (
            <div className="space-y-4">
              <div className="flex flex-col items-center justify-center py-8">
                <CheckCircle2 className="w-16 h-16 text-green-500 mb-4" />
                <h3 className="text-xl font-semibold mb-2">Integration Configured!</h3>
                <p className="text-gray-600 text-center">
                  {provider.display_name} has been successfully configured and is ready to use.
                </p>
              </div>

              <div className="flex gap-2">
                <Button type="button" className="flex-1" onClick={handleComplete}>
                  Done
                </Button>
              </div>
            </div>
          )}
        </form>
      </DialogContent>
    </Dialog>
  );
}
