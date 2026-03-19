import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Calendar, Share2, Search, ArrowRight, Bookmark, Zap, Target, TrendingUp, Cpu, Shield, Briefcase, Layers } from 'lucide-react';
import { Story, RelatedStory } from '@/types';
import api from '@/lib/api';
import { cn, generateGradient } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';

interface DeepDiveModalProps {
    isOpen: boolean;
    onClose: () => void;
    storyId: string;
    initialStory?: Story;
    activePersona?: string;
}

// ------------------------------------------------------------------
// HELPER FUNCTIONS (Shared Logic)
// ------------------------------------------------------------------
const getCategoryGradient = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes('model') || cat.includes('llm')) return 'from-blue-600 to-indigo-600';
    if (cat.includes('rag') || cat.includes('agent')) return 'from-emerald-500 to-teal-600';
    if (cat.includes('compute') || cat.includes('hardware')) return 'from-orange-500 to-red-600';
    if (cat.includes('business') || cat.includes('enterprise')) return 'from-slate-700 to-gray-900';
    if (cat.includes('demo') || cat.includes('creative')) return 'from-pink-500 to-rose-600';
    if (cat.includes('policy') || cat.includes('safety')) return 'from-amber-400 to-orange-500';
    return 'from-blue-500 to-cyan-500'; // Default
};

const getCategoryTheme = (category: string) => {
    const cat = category.toLowerCase();
    // Returns: { text, bg, border, icon }
    if (cat.includes('model')) return { text: 'text-blue-700', bg: 'bg-blue-50/80', border: 'border-blue-100', icon: 'text-blue-600', dot: 'bg-blue-500' };
    if (cat.includes('agent')) return { text: 'text-emerald-800', bg: 'bg-emerald-50/80', border: 'border-emerald-100', icon: 'text-emerald-600', dot: 'bg-emerald-500' };
    if (cat.includes('compute')) return { text: 'text-orange-800', bg: 'bg-orange-50/80', border: 'border-orange-100', icon: 'text-orange-600', dot: 'bg-orange-500' };
    if (cat.includes('business')) return { text: 'text-slate-800', bg: 'bg-slate-50/80', border: 'border-slate-200', icon: 'text-slate-600', dot: 'bg-slate-500' };
    if (cat.includes('policy')) return { text: 'text-amber-800', bg: 'bg-amber-50/80', border: 'border-amber-100', icon: 'text-amber-600', dot: 'bg-amber-500' };
    return { text: 'text-gray-800', bg: 'bg-gray-50', border: 'border-gray-100', icon: 'text-gray-500', dot: 'bg-gray-500' };
};

const getCategoryIcon = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes('model')) return Layers;
    if (cat.includes('agent')) return Target;
    if (cat.includes('compute')) return Cpu;
    if (cat.includes('business')) return Briefcase;
    if (cat.includes('policy')) return Shield;
    return Zap;
}

export default function DeepDiveModal({ isOpen, onClose, storyId, initialStory, activePersona = 'builders' }: DeepDiveModalProps) {
    const [story, setStory] = useState<Story | null>(initialStory || null);
    const [loading, setLoading] = useState(!initialStory);
    const { user } = useAuth();
    const [isSaved, setIsSaved] = useState(false);
    const router = useRouter();

    useEffect(() => {
        if (isOpen && storyId) {
            fetchStoryDetails();
        }
    }, [isOpen, storyId]);

    const fetchStoryDetails = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/stories/${storyId}`);
            setStory(res.data);
            setIsSaved(res.data.is_saved || false);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const toggleSave = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!user || !story) return;

        try {
            if (isSaved) {
                await api.delete(`/stories/${story.id}/save`);
                setIsSaved(false);
            } else {
                await api.post(`/stories/${story.id}/save`);
                setIsSaved(true);
            }
        } catch (err) {
            console.error('Failed to toggle save', err);
        }
    };

    if (!isOpen) return null;

    const summary = story?.summaries?.find(s => s.persona.toLowerCase() === activePersona.toLowerCase()) || story?.summaries?.[0];
    const category = summary?.category || "Technology";
    const gradientColors = getCategoryGradient(category);
    const theme = getCategoryTheme(category);
    const CategoryIcon = getCategoryIcon(category);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
                    >
                        {/* Backdrop */}
                        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

                        {/* Modal Content */}
                        <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col pointer-events-auto">

                            {/* CLOSE BUTTON */}
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 z-20 p-2 bg-white/20 hover:bg-white/40 rounded-full text-white transition-colors backdrop-blur-md"
                            >
                                <X size={20} />
                            </button>

                            {loading ? (
                                <div className="flex-1 flex items-center justify-center min-h-[400px]">
                                    <div className="flex flex-col items-center gap-3">
                                        <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                                        <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Loading Intelligence...</span>
                                    </div>
                                </div>
                            ) : story ? (
                                <>
                                    {/* 1. COMPACT HEADER (Unified Theme) */}
                                    <div className={cn("w-full min-h-[180px] md:min-h-[220px] shrink-0 relative flex flex-col justify-end p-6 md:p-8 bg-gradient-to-br", gradientColors)}>

                                        {/* Metadata Row (Top Left) */}
                                        <div className="absolute top-6 left-6 md:left-8 flex items-center gap-3">
                                            {story.items[0]?.source && (
                                                <div className="px-2 py-0.5 bg-white/20 backdrop-blur-md rounded text-[10px] font-bold uppercase tracking-wider text-white border border-white/10">
                                                    {story.items[0].source.name}
                                                </div>
                                            )}
                                            <span className="text-white/60 text-[11px] font-medium">
                                                {new Date(story.created_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric' })}
                                            </span>
                                        </div>

                                        {/* Title */}
                                        <h1 className="relative z-10 text-xl md:text-3xl font-black tracking-tight text-white leading-tight drop-shadow-sm max-w-3xl">
                                            {story.canonical_title}
                                        </h1>

                                        {/* Source Link */}
                                        <div className="mt-3 flex items-center gap-4">
                                            {story.items[0] && (
                                                <a
                                                    href={story.items[0].url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="inline-flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-white/70 hover:text-white transition-colors"
                                                >
                                                    Read Full Source <ArrowRight size={10} />
                                                </a>
                                            )}
                                        </div>
                                    </div>

                                    {/* 2. SCROLLABLE CONTENT */}
                                    <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-white">
                                        <div className="max-w-3xl mx-auto flex flex-col gap-8">

                                            {/* WHY IT MATTERS (Insight Box) */}
                                            {summary && (
                                                <div className={cn("rounded-2xl p-6 border transition-colors", theme.bg, theme.border)}>
                                                    <div className="flex items-center gap-2.5 mb-3">
                                                        <CategoryIcon className={theme.icon} size={18} strokeWidth={2.5} />
                                                        <span className={cn("text-[10px] font-black uppercase tracking-widest", theme.text)}>Why It Matters</span>
                                                    </div>
                                                    <p className="text-base md:text-lg text-gray-900 leading-relaxed font-medium">
                                                        {summary.summary_short.replace(/^(Why [Ii]t [Mm]atters:?\\s*)/i, "").trim()}
                                                    </p>
                                                </div>
                                            )}

                                            {/* KEY TAKEAWAYS */}
                                            {summary && summary.summary_bullets.length > 0 && (
                                                <div className="space-y-4">
                                                    <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide border-b border-gray-100 pb-2">
                                                        Key Takeaways
                                                    </h3>
                                                    <ul className="space-y-4">
                                                        {summary.summary_bullets.map((bullet, i) => (
                                                            <li key={i} className="flex gap-4 items-start group">
                                                                <div className={cn("w-1.5 h-1.5 rounded-full mt-2 shrink-0 transition-transform group-hover:scale-125", theme.dot)} />
                                                                <span className="text-base text-gray-700 leading-relaxed">
                                                                    {bullet.split(/(\*\*.*?\*\*)/g).map((part, j) =>
                                                                        part.startsWith('**') && part.endsWith('**') ? (
                                                                            <strong key={j} className="text-gray-900 font-semibold">{part.slice(2, -2)}</strong>
                                                                        ) : part
                                                                    )}
                                                                </span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}

                                            {/* CONTEXT (Background) */}
                                            {summary && summary.why_it_matters && (
                                                <div className="mt-2 pt-6 border-t border-gray-100">
                                                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
                                                        Additional Context
                                                    </h3>
                                                    <div className="text-sm md:text-base text-gray-600 leading-relaxed space-y-4">
                                                        {summary.why_it_matters.split('\n').map((para, i) => (
                                                            <p key={i}>{para}</p>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center text-gray-400 py-20">Story not found.</div>
                            )}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
