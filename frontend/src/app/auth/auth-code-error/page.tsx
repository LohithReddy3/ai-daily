"use client";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { AlertCircle } from "lucide-react";

export default function AuthErrorPage() {
    const searchParams = useSearchParams();
    const error = searchParams.get("error");

    return (
        <div className="h-screen w-full bg-slate-950 text-white flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-slate-900 border border-red-900/50 rounded-2xl p-8 space-y-6 text-center">
                <div className="w-16 h-16 rounded-full bg-red-900/20 flex items-center justify-center mx-auto text-red-500">
                    <AlertCircle size={32} />
                </div>

                <div className="space-y-2">
                    <h1 className="text-2xl font-bold font-outfit">Verification Failed</h1>
                    <p className="text-slate-400">
                        {error || "We couldn't verify your email link. It may have expired or arguably already been used."}
                    </p>
                </div>

                <div className="space-y-3">
                    <Button asChild className="w-full bg-slate-800 hover:bg-slate-700">
                        <Link href="/">Return Home</Link>
                    </Button>
                </div>
            </div>
        </div>
    );
}
