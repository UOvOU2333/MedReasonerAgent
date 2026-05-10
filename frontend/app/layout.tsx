import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MedReasonerAgent",
  description: "Multi-agent medical reasoning trace UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
