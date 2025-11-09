import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HireIQ - AI-Driven Hiring Platform",
  description: "Transform your hiring process with AI-powered assessments",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="bg-white">
      <body className={`${inter.className} bg-white`}>
        <AuthProvider>
          <div className="relative z-[20]">
            <Navbar />
          </div>
          <div className="relative z-[10]">
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
