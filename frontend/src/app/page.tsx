"use client";
import React, { useEffect, useState, Suspense } from 'react';
import api from '@/lib/api';
import { Persona, Story } from '@/types';
import StoryCard from '@/components/StoryCard';
import ProfileModal from '@/components/ProfileModal';
import DeepDiveModal from '@/components/DeepDiveModal';
import TrendsView from '@/components/TrendsView';
import { Code2, Briefcase, FlaskConical, RefreshCw, X, Menu, Lightbulb, Loader2, Newspaper, Compass, Bookmark, Settings, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/context/AuthContext';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';

function HomeContent() {
    const { user, signOut, openAuthModal } = useAuth(); // Destructure signOut
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();
    const activeStoryId = searchParams.get('story');

    // State from URL
    const activePersona = (searchParams.get('persona') as Persona) || 'builders';
    const activeCategory = searchParams.get('category');
    const activeTimeframe = (searchParams.get('timeframe') as 'today' | '7d' | '30d') || 'today';

    // Local State
    const [stories, setStories] = useState<Story[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [activeView, setActiveView] = useState<'feed' | 'saved' | 'brief' | 'trends'>('feed');
    const [brief, setBrief] = useState<any>(null);

    // Initial load check for saved view
    useEffect(() => {
        if (searchParams.get('view') === 'saved') {
            setActiveView('saved');
        } else if (searchParams.get('view') === 'trends') {
            setActiveView('trends');
        }
    }, []);

    const updateParams = (updates: Record<string, string | null>) => {
        const params = new URLSearchParams(searchParams.toString());
        Object.entries(updates).forEach(([key, value]) => {
            if (value === null) {
                params.delete(key);
            } else {
                params.set(key, value);
            }
        });
        router.push(`${pathname}?${params.toString()}`);
    };

    const handleCloseDeepDive = () => {
        updateParams({ story: null });
    };

    const primaryNav = [
        {
            id: 'brief',
            label: 'Brief',
            icon: Newspaper,
            action: () => {
                setActiveView('feed');
                // Reset to default state
                const params = new URLSearchParams();
                params.set('persona', 'builders');
                params.set('timeframe', 'today');
                router.push(`${pathname}?${params.toString()}`);
            }
        },
        {
            id: 'trends',
            label: 'Trends',
            icon: TrendingUp,
            action: () => {
                setActiveView('trends');
                updateParams({ view: 'trends' });
            }
        },
        {
            id: 'saved',
            label: 'Saved',
            icon: Bookmark,
            action: () => {
                setActiveView('saved');
                updateParams({ view: 'saved' });
            }
        },
    ];

    // We only need the top 5 stories for this specific layout
    const visibleStories = stories.slice(0, 5);

    const fetchStories = async () => {
        setLoading(true);
        setError('');
        try {
            if (activeView === 'saved') {
                if (!user) {
                    setStories([]);
                    setLoading(false);
                    return;
                }
                const res = await api.get('/stories/saved/all');
                setStories(res.data);
            } else if (activeView === 'brief') {
                // ... (brief logic kept same)
                try {
                    const res = await api.get(`/brief/today?persona=${activePersona}`);
                    setBrief(res.data);
                    setStories([]);
                } catch (e) {
                    console.log("Brief not ready, falling back to feed");
                    setActiveView('feed');
                    return;
                }
            } else if (activeView === 'trends') {
                // Trends view handles its own data fetching
                setLoading(false);
                return;
            } else {
                const params = new URLSearchParams({
                    timeframe: activeTimeframe,
                    limit: '100',
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
    }, [activePersona, activeCategory, activeView, activeTimeframe, user]);

    const [isSidebarOpen, setSidebarOpen] = useState(false);
    const [isProfileOpen, setProfileOpen] = useState(false);

    const hierarchy: Record<Persona, { label: string; icon: any; color: string; categories: { label: string; value: string }[] }> = {
        builders: {
            label: 'Builders',
            icon: Code2,
            color: 'text-blue-400',
            categories: [
                { label: "LLM Systems", value: "Models,RAG & Agents" },
                { label: "Research Papers", value: "Papers" },
                { label: "Open Source", value: "Open Source" }
            ]
        },
        executors: {
            label: 'Executors',
            icon: Briefcase,
            color: 'text-emerald-400',
            categories: [
                { label: "Market & Strategy", value: "Markets,Strategy" },
                { label: "Enterprise AI", value: "Enterprise,Industry" },
                { label: "Startups & Funding", value: "Startups" },
                { label: "Compute & Infra", value: "Compute" }
            ]
        },
        explorers: {
            label: 'Explorers',
            icon: FlaskConical,
            color: 'text-purple-400',
            categories: [
                { label: "AGI & Future", value: "AGI & Future" },
                { label: "Society & Ethics", value: "Ethics,Jobs & Society,Policy" },
                { label: "Creative AI", value: "Demos & Creativity" }
            ]
        }
    };

    const personas = Object.entries(hierarchy) as [Persona, typeof hierarchy['builders']][];
    const activePersonaData = hierarchy[activePersona];

    return (
        <div className="h-screen w-full bg-background text-foreground font-sans overflow-hidden flex flex-col">
            {/* Header - Light Neutral */}
            <header className="h-14 border-b border-gray-100 flex items-center justify-between px-6 bg-white z-50 flex-none shadow-sm">
                <div className="flex items-center gap-6">
                    {/* Sidebar Toggle */}
                    <button
                        onClick={() => setSidebarOpen(!isSidebarOpen)}
                        className="p-2 -ml-2 text-muted-foreground hover:bg-gray-50 rounded-full transition-colors"
                    >
                        <Menu size={18} className={cn("transition-transform", isSidebarOpen ? "rotate-90" : "")} />
                    </button>

                    <div className="text-sm font-black tracking-tighter cursor-pointer text-black" onClick={() => {
                        setActiveView('feed');
                        updateParams({ persona: 'builders', category: null });
                    }}>
                        AI<span className="text-gray-300">DAILY</span>
                    </div>

                    <div className="h-3 w-px bg-gray-100" />

                    {/* Current Context Indicator */}
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider">
                        {activeView === 'saved' ? (
                            <span className="text-yellow-600">Saved Stories</span>
                        ) : activeView === 'trends' ? (
                            <span className="text-purple-600">Market Trends</span>
                        ) : (
                            <>
                                <span className="text-black">{activePersonaData.label}</span>
                                {activeCategory && (
                                    <>
                                        <span className="text-gray-300">/</span>
                                        <span className="text-blue-600">{activeCategory}</span>
                                    </>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Timeframe Selector - Only show in Feed view */}
                    {activeView === 'feed' && (
                        <div className="flex bg-gray-100 rounded-lg p-0.5 border border-gray-200">
                            {(['today', '7d', '30d'] as const).map((tf) => (
                                <button
                                    key={tf}
                                    onClick={() => updateParams({ timeframe: tf })}
                                    className={cn(
                                        "px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-md transition-all",
                                        activeTimeframe === tf
                                            ? "bg-white text-black shadow-sm"
                                            : "text-gray-500 hover:text-black hover:bg-gray-200/50"
                                    )}
                                >
                                    {tf === 'today' ? 'Today' : tf}
                                </button>
                            ))}
                        </div>
                    )}

                    <button
                        onClick={fetchStories}
                        className="p-1.5 rounded-md text-gray-400 hover:text-black hover:bg-gray-100 transition-all"
                    >
                        <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                    </button>

                    <div className="text-[10px] font-mono text-gray-300 hidden md:block border-l border-gray-200 pl-4 h-4 flex items-center">
                        EST. 2024
                    </div>
                </div>
            </header>

            {/* CONTENT AREA: SIDEBAR + MAIN */}
            <div className="flex-1 flex overflow-hidden relative bg-gray-50/50">
                {/* PUSH SIDEBAR */}
                <AnimatePresence mode="wait">
                    {isSidebarOpen && (
                        <motion.aside
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 320, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                            className="bg-white border-r border-gray-100 shadow-xl flex flex-col overflow-hidden whitespace-nowrap z-40 absolute h-full md:static md:h-auto"
                        >
                            <div className="h-14 flex-none flex items-center justify-between px-6 border-b border-border min-w-[320px]">
                                <span className="text-sm font-black tracking-tighter text-black">AI<span className="text-gray-400">DAILY</span></span>
                                <button onClick={() => setSidebarOpen(false)} className="p-2 -mr-2 text-gray-400 hover:text-black">
                                    <X size={18} />
                                </button>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6 space-y-8 min-w-[320px]">
                                {/* PRIMARY NAV */}
                                <div className="space-y-1">
                                    {primaryNav.map((item) => {
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={item.action}
                                                className={cn("w-full flex items-center gap-3 text-left p-2 rounded-lg transition-colors group",
                                                    (activeView === item.id) ? "bg-gray-100 text-black" : "hover:bg-gray-50 text-gray-500"
                                                )}
                                            >
                                                <item.icon size={18} className={cn("transition-colors", (activeView === item.id) ? "text-yellow-600" : "text-gray-400 group-hover:text-black")} />
                                                <span className={cn("text-sm font-bold uppercase tracking-wider transition-colors", (activeView === item.id) ? "text-black" : "group-hover:text-black")}>{item.label}</span>
                                            </button>
                                        )
                                    })}
                                </div>

                                <div className="h-px bg-gray-100" />

                                {/* PERSONAS (Only show if NOT in saved mode? Or allow switching back?) */}
                                {/* Let's keep them, clicking them switches back to feed */}
                                <div className="space-y-4">
                                    <div className="text-[10px] font-black uppercase tracking-widest text-gray-400 px-2">Perspectives</div>
                                    {personas.map(([id, info]) => {
                                        const isActive = activePersona === id && activeView === 'feed';
                                        return (
                                            <div key={id} className="space-y-3">
                                                <button
                                                    onClick={() => {
                                                        setActiveView('feed');
                                                        // If clicking the active persona again, maybe clear category?
                                                        // For now, always switch persona and clear active category if not same
                                                        updateParams({ persona: id, category: null });
                                                    }}
                                                    className={cn(
                                                        "w-full flex items-center gap-3 text-left group px-2",
                                                        isActive ? "text-black" : "text-gray-500 hover:text-black"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "p-1.5 rounded-md transition-colors",
                                                        isActive ? "bg-black text-white" : "bg-gray-100 group-hover:bg-gray-200"
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
                                                            onClick={() => { updateParams({ category: null }); }}
                                                            className={cn(
                                                                "block w-full text-left text-[11px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                                !activeCategory ? "text-blue-600" : "text-gray-400 hover:text-black"
                                                            )}
                                                        >
                                                            All Stories
                                                        </button>
                                                        {info.categories.map(cat => (
                                                            <button
                                                                key={cat.label}
                                                                onClick={() => updateParams({ category: cat.value })}
                                                                className={cn(
                                                                    "block w-full text-left text-[11px] font-bold uppercase tracking-wider py-1.5 transition-colors",
                                                                    activeCategory === cat.value ? "text-blue-600" : "text-gray-400 hover:text-black"
                                                                )}
                                                            >
                                                                {cat.label}
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
                            <div className="p-6 border-t border-border bg-gray-50/50">
                                {user ? (
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs ring-1 ring-blue-200">
                                            {user.email?.[0].toUpperCase()}
                                        </div>
                                        <div className="flex-1 min-w-0 cursor-pointer group" onClick={() => setProfileOpen(true)}>
                                            <div className="text-xs font-medium text-black truncate">{user.email}</div>
                                            <div className="text-[10px] text-gray-500 group-hover:text-black uppercase tracking-wider font-bold mt-0.5 transition-colors">
                                                View Profile
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <button
                                        onClick={openAuthModal}
                                        className="w-full py-2 bg-white hover:bg-gray-50 rounded border border-gray-200 text-xs font-bold uppercase tracking-wider text-gray-600"
                                    >
                                        Sign In
                                    </button>
                                )}
                            </div>
                        </motion.aside>
                    )}
                </AnimatePresence>

                {/* MOBILE BACKDROP OVERLAY */}
                <AnimatePresence>
                    {isSidebarOpen && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSidebarOpen(false)}
                            className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm md:hidden"
                        />
                    )}
                </AnimatePresence>

                {/* MAIN LAYOUT: Pushes with sidebar only on desktop */}
                <main
                    onClick={() => isSidebarOpen && setSidebarOpen(false)}
                    className={cn(
                        "flex-1 w-full min-h-0 flex flex-col p-3 gap-3 bg-background transition-all duration-300 md:overflow-hidden overflow-y-auto",
                        isSidebarOpen ? "md:opacity-80" : ""
                    )}
                >
                    {activeView === 'trends' ? (
                        <div className="flex-1 overflow-y-auto">
                            <TrendsView />
                        </div>
                    ) : loading ? (
                        <div className="flex-1 flex flex-col items-center justify-center gap-6 bg-white rounded-2xl shadow-sm border border-gray-100">
                            <Loader2 className="animate-spin text-gray-300" size={48} />
                            <p className="text-[10px] uppercase tracking-[0.3em] text-gray-400 font-bold animate-pulse">
                                Establishing Uplink
                            </p>
                        </div>
                    ) : error ? (
                        <div className="flex-1 flex items-center justify-center bg-white rounded-2xl shadow-sm border border-gray-100">
                            <div className="text-red-500 text-xs font-mono uppercase tracking-widest bg-red-50 p-4 rounded border border-red-100">{error}</div>
                        </div>
                    ) : (
                        <>
                            {/* TOP ROW: 2 Stories (50% height) */}
                            <section className="h-[50%] w-full rounded-2xl shadow-sm border border-gray-100 overflow-hidden shrink-0 min-h-0">
                                <div className="h-full w-full grid grid-cols-1 md:grid-cols-2 bg-gray-100 gap-px">
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
                                    {/* Fill empty slots with clean blank frames instead of 'Offline' errors */}
                                    {Array.from({ length: Math.max(0, 2 - visibleStories.slice(0, 2).length) }).map((_, i) => (
                                        <div key={`empty-top-${i}`} className="bg-white border-r border-gray-100 last:border-0 relative">
                                            {/* Intentionally left blank to preserve grid layout gracefully */}
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* BOTTOM ROW: 3 Stories (50% height) */}
                            <section className="h-[50%] w-full rounded-2xl shadow-sm border border-gray-100 overflow-hidden shrink-0 min-h-0">
                                <div className="h-full w-full grid grid-cols-1 md:grid-cols-3 bg-gray-100 gap-px">
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
                                    {/* Fill empty slots with clean blank frames instead of 'Offline' errors */}
                                    {Array.from({ length: Math.max(0, 3 - visibleStories.slice(2, 5).length) }).map((_, i) => (
                                        <div key={`empty-btm-${i}`} className="bg-white border-r border-gray-100 last:border-0 relative">
                                            {/* Intentionally left blank to preserve grid layout gracefully */}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </>
                    )}
                </main>
            </div>

            {/* MODALS */}
            <ProfileModal isOpen={isProfileOpen} onClose={() => setProfileOpen(false)} />

            <DeepDiveModal
                isOpen={!!activeStoryId}
                onClose={handleCloseDeepDive}
                storyId={activeStoryId || ''}
                activePersona={activePersona}
            />
        </div>
    );
}

export default function Home() {
    return (
        <Suspense fallback={
            <div className="h-screen w-full flex items-center justify-center bg-background">
                <Loader2 className="animate-spin text-gray-300" size={48} />
            </div>
        }>
            <HomeContent />
        </Suspense>
    );
}
