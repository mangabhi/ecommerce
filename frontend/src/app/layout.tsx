import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "nook. — Thoughtful finds for everyday living",
  description:
    "Discover thoughtful everyday finds, shop the collection, and keep your orders close.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
