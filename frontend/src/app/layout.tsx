import type { Metadata } from "next";
import { DM_Sans, Plus_Jakarta_Sans, Fira_Code, Noto_Sans_Bengali } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages, getTranslations } from "next-intl/server";
import { Analytics } from "@/components/Analytics";
import "./globals.css";
import { Providers } from './providers'

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
});

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
});

// DM Sans and Plus Jakarta Sans have no Bengali glyphs. Without this, Bengali text falls back to
// whatever the OS provides and looks different (or breaks) from device to device. The browser
// picks glyphs per character, so Latin keeps its own face and Bengali uses Noto Sans Bengali.
const notoSansBengali = Noto_Sans_Bengali({
  variable: "--font-noto-bengali",
  subsets: ["bengali"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
});

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("publicMetaUi.default");
  return {
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
    title: { default: t("title"), template: "%s · AltCare" },
    description: t("description"),
    openGraph: { siteName: "AltCare", type: "website", title: t("title"), description: t("description") },
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      className={`${dmSans.variable} ${plusJakarta.variable} ${notoSansBengali.variable} ${firaCode.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <meta name="theme-color" content="#0f172a" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                // Two themes only (light / dark); the app never follows the OS. Default: light.
                // A legacy stored "system" is resolved once so nobody's look changes suddenly.
                const stored = localStorage.getItem('theme-storage');
                let theme = 'light';
                if (stored) {
                  const saved = (JSON.parse(stored).state || {}).theme;
                  theme = saved === 'dark' ? 'dark'
                    : saved === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark'
                    : 'light';
                }
                document.documentElement.classList.add(theme);
              } catch (e) {
                document.documentElement.classList.add('light');
              }
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Providers>{children}</Providers>
          <Analytics />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
