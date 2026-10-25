import type { Metadata } from "next";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "nook. — Thoughtful finds for everyday living",
  description:
    "Discover thoughtful everyday finds, shop the collection, and keep your orders close.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body>
        {children}
        <ThemeToggle />
      </body>
    </html>
  );
}
