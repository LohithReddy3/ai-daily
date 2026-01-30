"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Check, Loader2, Mail, Eye, EyeOff } from "lucide-react";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
    const { signInWithPassword, signUp, signInWithGoogle, resendVerificationEmail } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [fullName, setFullName] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

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
                // Validation for Sign Up
                if (password !== confirmPassword) {
                    throw new Error("Passwords do not match");
                }
                if (!fullName.trim()) {
                    throw new Error("Full Name is required");
                }
                if (password.length < 8) {
                    throw new Error("Password must be at least 8 characters");
                }

                const { error } = await signUp(email, password, fullName);
                if (error) throw error;
                setSuccessMessage(`Confirmation link sent to ${email}. Please verify to log in.`);
            }
        } catch (err: any) {
            console.error("Auth Error:", err);
            // Better error message handling
            let msg = err.message || "An error occurred";
            if (msg.includes("rate limit")) msg = "Too many requests. Please wait a moment.";
            if (msg.includes("security purposes")) msg = "Please use a different password or email.";
            setError(msg);
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
                        <p className="text-xs text-slate-400">If you don't see it, check your spam folder.</p>
                        <Button variant="outline" onClick={onClose} className="w-full mt-2">
                            Close
                        </Button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                        {!isLogin && (
                            <div className="space-y-2">
                                <Label htmlFor="fullName">Full Name</Label>
                                <Input
                                    id="fullName"
                                    type="text"
                                    placeholder="John Doe"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    required
                                    className="bg-slate-800 border-slate-700 focus:border-blue-500"
                                />
                            </div>
                        )}

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
                        <div className="relative">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="bg-slate-800 border-slate-700 focus:border-blue-500 pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                                >
                                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                </button>
                            </div>
                            {!isLogin && (
                                <p className="text-xs text-slate-500 mt-1">Must be at least 8 characters</p>
                            )}
                        </div>

                        {!isLogin && (
                            <div className="space-y-2">
                                <Label htmlFor="confirmPassword">Confirm Password</Label>
                                <Input
                                    id="confirmPassword"
                                    type={showPassword ? "text" : "password"}
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    className="bg-slate-800 border-slate-700 focus:border-blue-500"
                                />
                            </div>
                        )}

                        {error && (
                            <div className="text-red-400 text-sm bg-red-950/20 p-3 rounded border border-red-900/50 flex flex-col gap-2">
                                <div className="flex flex-col gap-1">
                                    <span className="font-semibold">Error:</span>
                                    <span>{error}</span>
                                </div>
                                {(error.includes("already registered") || error.includes("User already registered")) && !isLogin && (
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={async () => {
                                            setLoading(true);
                                            // Use local state function not the one from hook inside callback if possible, 
                                            // actually we destructured it above so use that.
                                            const { error } = await resendVerificationEmail(email);
                                            setLoading(false);
                                            if (!error) {
                                                setSuccessMessage(`Verification email resent to ${email}. Check your spam folder.`);
                                                setError(null);
                                            } else {
                                                let msg = error.message;
                                                if (msg.includes("rate limit")) msg = "Please wait a minute before retrying.";
                                                setError(msg);
                                            }
                                        }}
                                        className="mt-1 border-red-800 text-red-400 hover:bg-red-900/30 hover:text-red-300"
                                    >
                                        Resend Verification Email
                                    </Button>
                                )}
                            </div>
                        )}

                        <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {isLogin ? "Sign In" : "Sign Up"}
                        </Button>

                        <div className="text-center text-sm">
                            <button
                                type="button"
                                onClick={() => { setIsLogin(!isLogin); setError(null); }}
                                className="text-slate-400 hover:text-white underline underline-offset-4"
                            >
                                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
                            </button>
                        </div>
                    </form>
                )}
            </DialogContent>
        </Dialog >
    );
}
