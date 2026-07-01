import type { Metadata, Viewport } from "next";
import { Inter, Sora, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { Toaster } from "react-hot-toast";
import { SWRConfig } from "swr";
import "@/app/globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "CodePulse AI — VSB Engineering College",
    template: "%s | CodePulse AI",
  },
  description:
    "AI-powered coding activity monitoring and analytics platform for VSB Engineering College. Track LeetCode progress, GitHub activity, performance scores, and placement readiness.",
  keywords: [
    "coding tracker",
    "LeetCode analytics",
    "GitHub activity",
    "placement readiness",
    "VSB Engineering College",
    "coding performance",
  ],
  openGraph: {
    type: "website",
    locale: "en_IN",
    siteName: "CodePulse AI",
  },
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0F172A" },
    { media: "(prefers-color-scheme: light)", color: "#F8FAFC" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${sora.variable} ${jetbrainsMono.variable}`}
    >
      <body className="font-body antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <SWRConfig value={{
            revalidateOnFocus: false,
            revalidateOnReconnect: false,
            shouldRetryOnError: false
          }}>
            {children}
          </SWRConfig>
          <Toaster
            position="top-right"
            toastOptions={{
              className:
                "!bg-dark-card !text-dark-text !border !border-dark-border !shadow-card",
              duration: 4000,
              style: { borderRadius: "0.75rem" },
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  );
}
