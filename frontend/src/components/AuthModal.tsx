"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Check, Loader2, Mail } from "lucide-react";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
    const { signInWithPassword, signUp, signInWithGoogle } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccessMessage(null);

        try {
            if (isLogin) {
                const { error } = await signInWithPassword(email, password);
                if (error) throw error;
                onClose();
            } else {
                const { error } = await signUp(email, password);
                if (error) throw error;
                setSuccessMessage("Check your email for the confirmation link!");
            }
        } catch (err: any) {
            setError(err.message || "An error occurred");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md bg-slate-900 text-slate-100 border-slate-800">
                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold font-outfit">
                        {isLogin ? "Welcome Back" : "Create Account"}
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        {isLogin
                            ? "Sign in to save stories and personalize your feed."
                            : "Join AI Daily to access exclusive features."}
                    </DialogDescription>
                </DialogHeader>

                {successMessage ? (
                    <div className="flex flex-col items-center justify-center p-6 space-y-4 text-center">
                        <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center text-green-500">
                            <Check className="w-6 h-6" />
                        </div>
                        <p className="text-slate-200">{successMessage}</p>
                        <Button variant="outline" onClick={onClose} className="w-full">
                            Close
                        </Button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="name@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="bg-slate-800 border-slate-700 focus:border-blue-500"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="bg-slate-800 border-slate-700 focus:border-blue-500"
                            />
                        </div>

                        {error && (
                            <div className="text-red-400 text-sm bg-red-950/20 p-2 rounded border border-red-900/50">
                                {error}
                            </div>
                        )}

                        <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {isLogin ? "Sign In" : "Sign Up"}
                        </Button>

                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <span className="w-full border-t border-slate-700" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-slate-900 px-2 text-slate-500">Or continue with</span>
                            </div>
                        </div>

                        <Button
                            type="button"
                            variant="outline"
                            className="w-full border-slate-700 hover:bg-slate-800"
                            onClick={signInWithGoogle}
                        >
                            <svg className="mr-2 h-4 w-4" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512">
                                <path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path>
                            </svg>
                            Google
                        </Button>

                        <div className="text-center text-sm">
                            <button
                                type="button"
                                onClick={() => setIsLogin(!isLogin)}
                                className="text-slate-400 hover:text-white underline underline-offset-4"
                            >
                                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
                            </button>
                        </div>
                    </form>
                )}
            </DialogContent>
        </Dialog>
    );
}
