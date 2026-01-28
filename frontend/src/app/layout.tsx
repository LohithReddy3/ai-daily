import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { cn } from "@/lib/utils";

import { CSPostHogProvider } from './providers';

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
    title: "AI Daily Intelligence",
    description: "Your daily brief of AI news, tailored to your persona.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" className="dark" suppressHydrationWarning>
            <body
                className={cn(inter.variable, outfit.variable, "font-sans bg-zinc-950 text-zinc-100 min-h-screen")}
                suppressHydrationWarning
            >
                <CSPostHogProvider>
                    {children}
                </CSPostHogProvider>
            </body>
        </html>
    );
}
