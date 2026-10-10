import { RegisterForm } from '@/components/auth/RegisterForm'

export default async function RegisterPage({
  searchParams,
}: {
  searchParams: Promise<{ plan?: string }>
}) {
  const { plan } = await searchParams
  return <RegisterForm plan={plan} />
}
