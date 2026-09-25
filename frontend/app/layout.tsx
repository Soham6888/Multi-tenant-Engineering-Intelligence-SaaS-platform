import type { Metadata } from "next";
import "@fontsource-variable/dm-sans";
import "@fontsource-variable/manrope";
import "./globals.css";
import "./workspace.css";

export const metadata: Metadata = {
  title: "Engineering Intelligence · Overview",
  description:
    "A clearer view of your engineering delivery. Local-first engineering intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
