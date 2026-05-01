#!/bin/bash
# AltCare Frontend Quick Start Script
# Run this from the project root: ./frontend-quickstart.sh

set -e  # Exit on error

echo "🚀 AltCare Frontend Quick Start"
echo "================================"
echo ""

# Check if backend is running
echo "📡 Checking backend connection..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "❌ Backend is not running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd backend && source venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    echo ""
    exit 1
fi

# Check if Node.js is installed
echo ""
echo "📦 Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node -v)
echo "✅ Node.js $NODE_VERSION found"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed!"
    exit 1
fi

NPM_VERSION=$(npm -v)
echo "✅ npm $NPM_VERSION found"

# Create frontend directory if it doesn't exist
if [ ! -d "frontend" ]; then
    echo ""
    echo "📂 Creating Next.js frontend project..."
    npx create-next-app@latest frontend \
        --typescript \
        --tailwind \
        --app \
        --src-dir \
        --import-alias "@/*" \
        --no-git

    echo "✅ Next.js project created"
else
    echo ""
    echo "✅ Frontend directory already exists"
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo ""
echo "📦 Installing dependencies..."

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found!"
    exit 1
fi

# Install core dependencies
echo "Installing core packages..."
npm install --silent \
    axios \
    react-query \
    zustand \
    date-fns \
    @hookform/resolvers \
    react-hook-form \
    zod \
    next-intl \
    js-cookie \
    react-hot-toast

# Install dev dependencies
echo "Installing dev dependencies..."
npm install --silent -D @types/js-cookie

# Initialize shadcn/ui
echo ""
echo "🎨 Setting up shadcn/ui..."

# Create components.json for shadcn/ui
cat > components.json <<EOF
{
  "\$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
EOF

# Install shadcn/ui components
echo "Installing UI components..."
npx shadcn-ui@latest add button --yes --overwrite
npx shadcn-ui@latest add input --yes --overwrite
npx shadcn-ui@latest add card --yes --overwrite
npx shadcn-ui@latest add table --yes --overwrite
npx shadcn-ui@latest add dialog --yes --overwrite
npx shadcn-ui@latest add dropdown-menu --yes --overwrite
npx shadcn-ui@latest add select --yes --overwrite
npx shadcn-ui@latest add label --yes --overwrite
npx shadcn-ui@latest add toast --yes --overwrite
npx shadcn-ui@latest add avatar --yes --overwrite
npx shadcn-ui@latest add badge --yes --overwrite
npx shadcn-ui@latest add tabs --yes --overwrite

# Create .env.local
echo ""
echo "⚙️  Setting up environment variables..."
cat > .env.local <<EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_TIMEOUT=30000

# Application
NEXT_PUBLIC_APP_NAME=AltCare
NEXT_PUBLIC_APP_VERSION=0.1.0
NEXT_PUBLIC_DEFAULT_LANGUAGE=en

# Feature Flags
NEXT_PUBLIC_FEATURE_2FA=true
NEXT_PUBLIC_FEATURE_BKASH=true
NEXT_PUBLIC_FEATURE_AI=false

# Development
NODE_ENV=development
EOF

echo "✅ Environment variables configured"

# Create directory structure
echo ""
echo "📁 Creating project structure..."

mkdir -p src/lib/api
mkdir -p src/lib/hooks
mkdir -p src/lib/utils
mkdir -p src/lib/constants
mkdir -p src/types
mkdir -p src/store
mkdir -p src/messages
mkdir -p src/components/ui
mkdir -p src/components/layout
mkdir -p src/components/auth
mkdir -p src/components/patients
mkdir -p src/components/shared
mkdir -p src/app/\(auth\)/login
mkdir -p src/app/\(dashboard\)/patients
mkdir -p public/images
mkdir -p public/icons

echo "✅ Directory structure created"

# Create initial translation files
echo ""
echo "🌍 Creating translation files..."

cat > src/messages/en.json <<'EOF'
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "loading": "Loading...",
    "error": "An error occurred"
  },
  "auth": {
    "login": "Login",
    "logout": "Logout",
    "email": "Email",
    "password": "Password",
    "loginSuccess": "Login successful",
    "loginFailed": "Login failed"
  },
  "patients": {
    "title": "Patients",
    "addPatient": "Add Patient",
    "editPatient": "Edit Patient",
    "firstName": "First Name",
    "lastName": "Last Name",
    "phone": "Phone",
    "gender": "Gender",
    "male": "Male",
    "female": "Female",
    "other": "Other"
  }
}
EOF

cat > src/messages/bn.json <<'EOF'
{
  "common": {
    "save": "সংরক্ষণ করুন",
    "cancel": "বাতিল করুন",
    "delete": "মুছুন",
    "edit": "সম্পাদনা",
    "search": "অনুসন্ধান",
    "loading": "লোড হচ্ছে...",
    "error": "একটি ত্রুটি ঘটেছে"
  },
  "auth": {
    "login": "লগইন",
    "logout": "লগআউট",
    "email": "ইমেইল",
    "password": "পাসওয়ার্ড",
    "loginSuccess": "সফলভাবে লগইন হয়েছে",
    "loginFailed": "লগইন ব্যর্থ হয়েছে"
  },
  "patients": {
    "title": "রোগীরা",
    "addPatient": "রোগী যোগ করুন",
    "editPatient": "রোগী সম্পাদনা করুন",
    "firstName": "প্রথম নাম",
    "lastName": "শেষ নাম",
    "phone": "ফোন",
    "gender": "লিঙ্গ",
    "male": "পুরুষ",
    "female": "মহিলা",
    "other": "অন্যান্য"
  }
}
EOF

echo "✅ Translation files created"

# Update next.config.js
echo ""
echo "⚙️  Updating Next.js configuration..."

cat > next.config.js <<'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // API endpoint rewrite for local development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ]
  },

  // Environment variables available to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Image optimization
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig
EOF

echo "✅ Next.js configuration updated"

# Summary
echo ""
echo "================================================"
echo "✅ Frontend setup complete!"
echo "================================================"
echo ""
echo "📂 Project structure:"
echo "   - src/app/           → Next.js pages (App Router)"
echo "   - src/components/    → React components"
echo "   - src/lib/           → API client, hooks, utils"
echo "   - src/types/         → TypeScript types"
echo "   - src/store/         → Zustand state management"
echo "   - src/messages/      → i18n translations (EN/BN)"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Start the development server:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "2. Open http://localhost:3000 in your browser"
echo ""
echo "3. Read the setup guide:"
echo "   cat ../FRONTEND_SETUP.md"
echo ""
echo "4. Start building! Recommended order:"
echo "   - Authentication (login, 2FA)"
echo "   - Dashboard layout (sidebar, header)"
echo "   - Patient management (CRUD)"
echo "   - Other modules"
echo ""
echo "📚 Documentation:"
echo "   - FRONTEND_SETUP.md → Complete setup guide"
echo "   - Next.js Docs → https://nextjs.org/docs"
echo "   - shadcn/ui → https://ui.shadcn.com"
echo ""
echo "Happy coding! 🎉"
