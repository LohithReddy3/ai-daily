"use client";
import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { createClient } from '@/lib/supabase';
import api from '@/lib/api';
import posthog from 'posthog-js';
import AuthModal from '@/components/AuthModal';

type AuthContextType = {
    user: User | null;
    session: Session | null;
    loading: boolean;
    signInWithGoogle: () => Promise<void>;
    signInWithEmail: (email: string) => Promise<{ error: any }>;
    signInWithPassword: (email: string, password: string) => Promise<{ error: any }>;
    signUp: (email: string, password: string, full_name: string) => Promise<{ error: any }>;
    verifyOtp: (email: string, token: string) => Promise<{ error: any; session: Session | null }>;
    signOut: () => Promise<void>;
    openAuthModal: () => void;
    closeAuthModal: () => void;
};

const AuthContext = createContext<AuthContextType>({
    user: null,
    session: null,
    loading: true,
    signInWithGoogle: async () => { },
    signInWithEmail: async () => ({ error: null }),
    signInWithPassword: async () => ({ error: null }),
    signUp: async () => ({ error: null }),
    verifyOtp: async () => ({ error: null, session: null }),
    signOut: async () => { },
    openAuthModal: () => { alert("DEBUG: Default Context (Not Connected)"); },
    closeAuthModal: () => { },
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);
    const supabase = createClient();

    useEffect(() => {
        // Initial Session Check
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
            if (session?.user) {
                posthog.identify(session.user.id, { email: session.user.email });
            }
        });

        // Listen for changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);

            if (session?.access_token) {
                // Configure axios to send token
                api.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
            } else {
                delete api.defaults.headers.common['Authorization'];
            }

            if (session?.user) {
                posthog.identify(session.user.id, { email: session.user.email });
            } else {
                posthog.reset();
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    const signInWithGoogle = async () => {
        await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`,
            },
        });
    };

    const signInWithEmail = async (email: string) => {
        const { error } = await supabase.auth.signInWithOtp({
            email,
            options: {
                emailRedirectTo: `${window.location.origin}`,
            }
        });
        return { error };
    };

    const signInWithPassword = async (email: string, password: string) => {
        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        return { error };
    };

    const signUp = async (email: string, password: string, full_name: string) => {
        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: full_name,
                },
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            }
        });
        return { error };
    };

    const verifyOtp = async (email: string, token: string) => {
        const { data, error } = await supabase.auth.verifyOtp({
            email,
            token,
            type: 'email'
        });
        return { error, session: data.session };
    };

    const signOut = async () => {
        await supabase.auth.signOut();
        posthog.reset();
    };

    const [isModalOpen, setIsModalOpen] = useState(false);
    const openAuthModal = () => { alert("DEBUG: Provider Function Called"); setIsModalOpen(true); };
    const closeAuthModal = () => { setIsModalOpen(false); };

    return (
        <AuthContext.Provider value={{
            user, session, loading,
            signInWithGoogle, signInWithEmail, verifyOtp, signOut,
            signInWithPassword, signUp,
            openAuthModal, closeAuthModal
        }}>
            {children}
            {isModalOpen && (
                <div style={{ position: 'fixed', top: 0, left: 0, width: '100px', height: '100px', background: 'red', zIndex: 999999, content: 'DEBUG' }}>
                    DEBUG: OPEN
                </div>
            )}
            <AuthModal isOpen={isModalOpen} onClose={closeAuthModal} />
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
