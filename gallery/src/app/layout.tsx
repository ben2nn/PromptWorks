import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { NoFlashProvider, ThemeScript } from "@/components/NoFlashProvider";

export const metadata: Metadata = {
  title: "Prompt Gallery - 提示词画廊",
  description: "探索和分享优质的 AI 提示词",
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" }
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="loading">
      <head>
        <ThemeScript />
        <meta name="color-scheme" content="light dark" />
        <style dangerouslySetInnerHTML={{
          __html: `
            /* 防闪屏的关键 CSS - 立即生效 */
            html { background-color: #ffffff; }
            @media (prefers-color-scheme: dark) {
              html { background-color: #0f172a; }
            }
            body.loading { opacity: 0; }
            body.loaded { opacity: 1; transition: opacity 0.3s ease-out; }
          `
        }} />
      </head>
      <body className="antialiased loading">
        <NoFlashProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </NoFlashProvider>
      </body>
    </html>
  );
}
