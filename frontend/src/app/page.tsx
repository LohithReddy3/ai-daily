"use client";
import React, { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Persona, Story } from '@/types';
import StoryCard from '@/components/StoryCard';
import ProfileModal from '@/components/ProfileModal';
import { Code2, Briefcase, FlaskConical, RefreshCw, X, Menu, Lightbulb, Loader2, Newspaper, Compass, Bookmark, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';

export default function Home() {
    const { user, signOut, openAuthModal } = useAuth(); // Destructure signOut
    const [stories, setStories] = useState<Story[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activePersona, setActivePersona] = useState<Persona>('builders');
    const [activeCategory, setActiveCategory] = useState<string | null>(null);
    const [activeView, setActiveView] = useState<'feed' | 'saved'>('feed'); // New State

    const primaryNav = [
        { id: 'brief', label: 'Brief', icon: Newspaper, action: () => { setActiveView('feed'); setActivePersona('builders'); } },
        { id: 'saved', label: 'Saved', icon: Bookmark, action: () => { setActiveView('saved'); setActiveCategory(null); } },
        // Settings removed for now or can be just a placeholder
    ];
    // We only need the top 5 stories for this specific layout
    const visibleStories = stories.slice(0, 5);

    const fetchStories = async () => {
        setLoading(true);
        setError('');
        try {
            if (activeView === 'saved') {
                if (!user) {
                    setStories([]); // Or show "Login to see saved" message
                    setLoading(false);
                    return;
                }
                const res = await api.get('/stories/saved/all');
                setStories(res.data);
            } else {
                const params = new URLSearchParams({
                    timeframe: 'today',
                    persona: activePersona,
                });
                if (activeCategory) params.append('category', activeCategory);

                const res = await api.get(`/stories/?${params.toString()}`);
                setStories(res.data);
            }
        } catch (err) {
            console.error(err);
            setError('Intelligence connection lost.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStories();
    }, [activePersona, activeCategory, activeView, user]); // Add dependencies

    const [isSidebarOpen, setSidebarOpen] = useState(false);
    const [isProfileOpen, setProfileOpen] = useState(false);

    const hierarchy: Record<Persona, { label: string; icon: any; color: string; categories: string[] }> = {
        builders: {
            label: 'Builders',
            icon: Code2,
            color: 'text-blue-400',
            categories: ["Models", "RAG & Agents", "Papers", "Open Source"]
        },
        executors: {
            label: 'Executors',
            icon: Briefcase,
            color: 'text-emerald-400',
            categories: ["Markets", "Enterprise", "Industry", "Policy", "Startups", "Strategy", "Compute"]
        },
        explorers: {
            label: 'Explorers',
            icon: FlaskConical,
            color: 'text-purple-400',
            categories: ["AGI & Future", "Ethics", "Jobs & Society", "Demos & Creativity"]
        },
        thought_leaders: {
            label: 'Insight',
            icon: Lightbulb,
            color: 'text-yellow-400',
            categories: ["Deep Dives", "Concepts", "Hot Takes"]
        }
    };

    const personas = Object.entries(hierarchy) as [Persona, typeof hierarchy['builders']][];
    const activePersonaData = hierarchy[activePersona];

    return (
        <div className="h-screen w-full bg-slate-950 text-white font-sans overflow-hidden flex flex-col selection:bg-[#004182]/30">
            {/* Header - Distinct Dark Neutral */}
            <header className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-slate-800 z-50 flex-none shadow-md">
                <div className="flex items-center gap-6">
                    {/* Sidebar Toggle */}
                    <button
                        onClick={() => setSidebarOpen(!isSidebarOpen)}
                        className="p-2 -ml-2 text-white/80 hover:bg-white/10 rounded-full transition-colors"
                    >
                        <Menu size={18} className={cn("transition-transform", isSidebarOpen ? "rotate-90" : "")} />
                    </button>

                    <div className="text-sm font-black tracking-tighter cursor-pointer" onClick={() => { setActiveView('feed'); setActivePersona('builders'); setActiveCategory(null); }}>
                        AI<span className="text-white/40">DAILY</span>
                    </div>

                    <div className="h-3 w-px bg-white/10" />

                    {/* Current Context Indicator */}
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider">
                        {activeView === 'saved' ? (
                            <span className="text-yellow-400">Saved Stories</span>
                        ) : (
                            <>
                                <span className="text-white">{activePersonaData.label}</span>
                                {activeCategory && (
                                    <>
                                        <span className="text-white/40">/</span>
                                        <span className="text-[#004182]">{activeCategory}</span>
                                    </>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={fetchStories}
                        className="p-1.5 rounded-md text-white/40 hover:text-white hover:bg-white/10 transition-all"
                    >
                        <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                    </button>

                    <div className="text-[10px] font-mono text-white/40 hidden md:block border-l border-white/10 pl-4 h-4 flex items-center">
                        EST. 2024
                    </div>
                </div>
            </header>

            {/* CONTENT AREA: SIDEBAR + MAIN */}
            <div className="flex-1 flex overflow-hidden relative">
                {/* PUSH SIDEBAR */}
                <AnimatePresence mode="wait">
                    {isSidebarOpen && (
                        <motion.aside
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 320, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            className="bg-slate-800 border-r border-white/10 shadow-2xl flex flex-col overflow-hidden whitespace-nowrap z-40"
                        >
                            <div className="h-14 flex-none flex items-center justify-between px-6 border-b border-white/10 min-w-[320px]">
                                <span className="text-sm font-black tracking-tighter text-white">AI<span className="text-white/40">DAILY</span></span>
                                <button onClick={() => setSidebarOpen(false)} className="p-2 -mr-2 text-white/40 hover:text-white">
                                    <X size={18} />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-8 min-w-[320px]">
                                {/* PRIMARY NAV */}
                                <div className="space-y-1">
                                    {primaryNav.map((item) => {
                                        const isActive = (activeView === 'saved' && item.id === 'saved') || (activeView === 'feed' && item.id !== 'saved' && item.id !== 'settings'); // Simple logic
                                        // Actually better logic:
                                        // If view is saved, only Saved is active.
                                        // If view is feed, maybe Brief/Explore are active?
                                        // For now let's just make them clickable.

                                        return (
                                            <button
                                                key={item.id}
                                                onClick={item.action}
                                                className={cn("w-full flex items-center gap-3 text-left p-2 rounded-lg transition-colors group",
                                                    (activeView === 'saved' && item.id === 'saved') ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60"
                                                )}
                                            >
                                                <item.icon size={18} className={cn("transition-colors", (activeView === 'saved' && item.id === 'saved') ? "text-yellow-400" : "text-white/40 group-hover:text-white")} />
                                                <span className={cn("text-sm font-bold uppercase tracking-wider transition-colors", (activeView === 'saved' && item.id === 'saved') ? "text-white" : "group-hover:text-white")}>{item.label}</span>
                                            </button>
                                        )
                                    })}
                                </div>

                                <div className="h-px bg-white/5" />

                                {/* PERSONAS (Only show if NOT in saved mode? Or allow switching back?) */}
                                {/* Let's keep them, clicking them switches back to feed */}
                                <div className="space-y-4">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-white/30 px-2">Perspectives</div>
                                    {personas.map(([id, info]) => {
                                        const isActive = activePersona === id && activeView === 'feed';
                                        return (
                                            <div key={id} className="space-y-3">
                                                <button
                                                    onClick={() => {
                                                        setActiveView('feed');
                                                        setActivePersona(id);
                                                        if (activePersona !== id) setActiveCategory(null);
                                                    }}
                                                    className={cn(
                                                        "w-full flex items-center gap-3 text-left group px-2",
                                                        isActive ? "text-white" : "text-white/40 hover:text-white"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "p-1.5 rounded-md transition-colors",
                                                        isActive ? "bg-white text-black" : "bg-white/5 group-hover:bg-white/10"
                                                    )}>
                                                        <info.icon size={14} />
                                                    </div>
                                                    <span className="text-base font-bold uppercase tracking-tight">{info.label}</span>
                                                </button>

                                                {isActive && (
                                                    <motion.div
                                                        initial={{ opacity: 0, height: 0 }}
                                                        animate={{ opacity: 1, height: "auto" }}
                                                        className="pl-11 space-y-1"
                                                    >
                                                        <button
                                                            onClick={() => { setActiveCategory(null); }}
                                                            className={cn(
                                                                "block w-full text-left text-[11px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                                !activeCategory ? "text-[#004182]" : "text-white/40 hover:text-white"
                                                            )}
                                                        >
                                                            All Stories
                                                        </button>
                                                        {info.categories.map(cat => (
                                                            <button
                                                                key={cat}
                                                                onClick={() => setActiveCategory(cat)}
                                                                className={cn(
                                                                    "block w-full text-left text-[11px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                                    activeCategory === cat ? "text-[#004182]" : "text-white/40 hover:text-white"
                                                                )}
                                                            >
                                                                {cat}
                                                            </button>
                                                        ))}
                                                    </motion.div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* USER / SIGN OUT SECTION */}
                            <div className="p-6 border-t border-white/10 bg-black/20">
                                {user ? (
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-xs ring-1 ring-blue-500/50">
                                            {user.email?.[0].toUpperCase()}
                                        </div>
                                        <div className="flex-1 min-w-0 cursor-pointer group" onClick={() => setProfileOpen(true)}>
                                            <div className="text-xs font-medium text-white/80 truncate">{user.email}</div>
                                            <div className="text-[10px] text-slate-400 group-hover:text-white uppercase tracking-wider font-bold mt-0.5 transition-colors">
                                                View Profile
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => {
                                            alert("Debug: Sidebar Clicked (page.tsx)");
                                            openAuthModal();
                                        }}
                                        className="w-full py-2 bg-white/5 hover:bg-white/10 rounded border border-white/10 text-xs font-bold uppercase tracking-wider text-white/60"
                                    >
                                        Sign In (Live)
                                    </button>
                                )}
                            </div>
                        </motion.aside>
                    )}
                </AnimatePresence>

                {/* MAIN LAYOUT: Pushes with sidebar, Closes on click */}
                <main
                    onClick={() => isSidebarOpen && setSidebarOpen(false)}
                    className={cn(
                        "flex-1 w-full min-h-0 flex flex-col p-4 gap-4 bg-slate-950 transition-all duration-300",
                        isSidebarOpen ? "cursor-pointer opacity-80" : ""
                    )}
                >
                    {loading ? (
                        <div className="flex-1 flex flex-col items-center justify-center gap-6 bg-slate-900 rounded-2xl shadow-sm border border-white/5">
                            <Loader2 className="animate-spin text-white/20" size={48} />
                            <p className="text-[10px] uppercase tracking-[0.3em] text-white/40 font-bold animate-pulse">
                                Establishing Uplink
                            </p>
                        </div>
                    ) : error ? (
                        <div className="flex-1 flex items-center justify-center bg-slate-900 rounded-2xl shadow-sm border border-white/5">
                            <div className="text-white/40 text-xs font-mono uppercase tracking-widest bg-red-500/10 p-4 rounded text-red-400">{error}</div>
                        </div>
                    ) : (
                        <>
                            {/* TOP ROW: 2 Stories (50% Height) */}
                            <section className="flex-1 min-h-0 w-full rounded-2xl shadow-2xl border border-white/5 overflow-hidden">
                                <div className="h-full w-full grid grid-cols-1 md:grid-cols-2 bg-slate-900 gap-px">
                                    <AnimatePresence mode="popLayout">
                                        {visibleStories.slice(0, 2).map((story, index) => (
                                            <StoryCard
                                                key={story.id}
                                                story={story}
                                                activePersona={activePersona}
                                                index={index}
                                            />
                                        ))}
                                    </AnimatePresence>
                                    {/* Fill empty slots */}
                                    {Array.from({ length: Math.max(0, 2 - visibleStories.slice(0, 2).length) }).map((_, i) => (
                                        <div key={`empty-top-${i}`} className="bg-slate-900 border-r border-white/5 last:border-0 relative group">
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                                <span className="text-[9px] uppercase tracking-widest text-white/10 font-black">Offline</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* BOTTOM ROW: 3 Stories (50% Height) */}
                            <section className="flex-1 min-h-0 w-full rounded-2xl shadow-2xl border border-white/5 overflow-hidden">
                                <div className="h-full w-full grid grid-cols-1 md:grid-cols-3 bg-slate-900 gap-px">
                                    <AnimatePresence mode="popLayout">
                                        {visibleStories.slice(2, 5).map((story, index) => (
                                            <StoryCard
                                                key={story.id}
                                                story={story}
                                                activePersona={activePersona}
                                                index={index + 2} // Continue index for colors
                                            />
                                        ))}
                                    </AnimatePresence>
                                    {/* Fill empty slots */}
                                    {Array.from({ length: Math.max(0, 3 - visibleStories.slice(2, 5).length) }).map((_, i) => (
                                        <div key={`empty-btm-${i}`} className="bg-slate-900 border-r border-white/5 last:border-0 relative group">
                                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                                <span className="text-[9px] uppercase tracking-widest text-white/10 font-black">Offline</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </>
                    )}
                </main>
            </div>

            <ProfileModal isOpen={isProfileOpen} onClose={() => setProfileOpen(false)} />
        </div>
    );
}
