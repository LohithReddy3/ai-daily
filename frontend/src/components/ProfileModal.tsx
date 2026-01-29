import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { LogOut, User as UserIcon, CheckCircle2, ShieldCheck } from "lucide-react";

interface ProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
    const { user, signOut } = useAuth();

    if (!user) return null;

    const initials = user.user_metadata?.full_name
        ? user.user_metadata.full_name.split(" ").map((n: string) => n[0]).join("").toUpperCase().substring(0, 2)
        : user.email?.substring(0, 2).toUpperCase();

    const handleSignOut = async () => {
        await signOut();
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md bg-[#001D38] text-white border-white/10 p-0 overflow-hidden gap-0">
                {/* Header Profile Section */}
                <div className="bg-[#002B52] p-8 text-center border-b border-white/10 relative">
                    <div className="absolute top-4 right-4">
                        <div className="inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 gap-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                            <ShieldCheck size={12} />
                            Verified Account
                        </div>
                    </div>

                    <div className="flex justify-center mb-4 mt-4">
                        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#FFD200] to-orange-500 p-[2px]">
                            <div className="w-full h-full rounded-full bg-[#002B52] flex items-center justify-center border-4 border-[#002B52]">
                                <span className="text-3xl font-bold font-outfit text-[#FFD200]">
                                    {initials}
                                </span>
                            </div>
                        </div>
                    </div>

                    <h2 className="text-2xl font-bold font-outfit text-white mb-1">
                        {user.user_metadata?.full_name || "Daily Reader"}
                    </h2>
                    <p className="text-slate-400 font-mono text-xs">
                        {user.email}
                    </p>
                </div>

                {/* Details Section */}
                <div className="p-6 space-y-6">
                    <div className="space-y-4">
                        <div className="bg-white/5 rounded-xl p-4 flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400">
                                <UserIcon size={20} />
                            </div>
                            <div>
                                <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Member Since</p>
                                <p className="text-sm font-medium">
                                    {new Date(user.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
                                </p>
                            </div>
                        </div>

                        <div className="bg-white/5 rounded-xl p-4 flex items-center gap-4 opacity-50 cursor-not-allowed">
                            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400">
                                <CheckCircle2 size={20} />
                            </div>
                            <div>
                                <p className="text-xs text-slate-400 uppercase tracking-wider font-bold">Subscription</p>
                                <p className="text-sm font-medium">Free Plan</p>
                            </div>
                        </div>
                    </div>

                    <div className="pt-2">
                        <Button
                            variant="destructive"
                            className="w-full bg-red-950/50 hover:bg-red-900/80 text-red-200 border-red-900/30 border h-12 gap-2"
                            onClick={handleSignOut}
                        >
                            <LogOut size={16} />
                            Sign Out
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
