"use client";
import React, { useState } from 'react';
import { Story, Persona } from '@/types';
import { cn } from '@/lib/utils';
import { Bookmark, X, ArrowRight, ArrowUpRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';

interface StoryCardProps {
    story: Story;
    activePersona: Persona;
    layoutId?: string;
    index?: number;
}

export default function StoryCard({ story, activePersona, layoutId, index = 0 }: StoryCardProps) {
    const [isSaved, setIsSaved] = useState(false);
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();

    // Check if this card is expanded based on URL
    const isExpanded = searchParams.get('story') === story.id;

    // Handle expansion via URL
    const handleExpand = () => {
        const params = new URLSearchParams(searchParams);
        params.set('story', story.id);
        router.push(`${pathname}?${params.toString()}`, { scroll: false });
    };

    // Handle close via URL (back)
    const handleClose = (e?: React.MouseEvent) => {
        e?.stopPropagation();
        router.back();
    };

    const summary = story.summaries.find(s => s.persona === activePersona);
    const hasSummary = !!summary;
    const date = new Date(story.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    // DEEP NAVY THEME
    // Base: #004182 (Deep Navy / LinkedIn Dark)
    // Hover: #002a5c (Midnight Blue)
    // Gold: #FFD200 (Keeping the accent)
    // Black: #000000
    const theme = {
        bg: 'bg-[#004182]', // Deep Navy
        hover: 'hover:bg-[#002a5c]', // Midnight Blue
        border: 'border-[#FFD200]', // Gold borders
        textHead: 'text-white',
        textSummary: 'text-white/95', // High contrast white
        accent: 'text-[#FFD200]', // Gold accents
        indicator: 'bg-[#FFD200]',
    };

    // Use a unique ID for layout animations
    const cardId = layoutId || `story-${story.id}`;

    return (
        <>
            {/* GRID CELL - DEEP NAVY */}
            <motion.div
                layoutId={cardId}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                onClick={handleExpand}
                className={cn(
                    "relative group cursor-pointer w-full h-full overflow-hidden hover:z-10",
                    "border-r border-b border-[#FFD200]/20 last:border-0 transition-colors duration-300",
                    "flex flex-col justify-between",
                    theme.bg,
                    theme.hover
                )}
            >
                {/* Top: Date & Category Indicator */}
                <div className="p-4 flex justify-between items-start z-10 w-full mix-blend-plus-lighter">
                    <div className="flex gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#FFD200] shadow-[0_0_8px_rgba(255,210,0,0.8)]" />
                        <div className="w-1.5 h-1.5 rounded-full bg-[#FFD200]/30" />
                        <div className="w-1.5 h-1.5 rounded-full bg-[#FFD200]/30" />
                    </div>
                    <span className="text-[10px] font-mono uppercase tracking-widest transition-colors font-bold text-[#FFD200] group-hover:text-white">
                        {date}
                    </span>
                </div>

                {/* Middle: HEADLINE & SUMMARY */}
                <div className="px-4 relative z-10 flex-1 min-h-0 flex flex-col justify-start pt-1 gap-2 overflow-hidden">
                    <motion.h2
                        layoutId={`${cardId}-title`}
                        className={cn(
                            "text-2xl lg:text-3xl font-black leading-[0.9] font-outfit uppercase tracking-tighter line-clamp-2 md:line-clamp-3 ml-[-1px]",
                            theme.textHead
                        )}
                        style={{ wordBreak: 'break-word' }}
                    >
                        {story.canonical_title}
                    </motion.h2>

                    {hasSummary && (
                        <motion.div
                            initial={{ opacity: 0.9 }}
                            whileHover={{ opacity: 1 }}
                            className="flex-1 overflow-hidden"
                        >
                            <p className={cn(
                                "text-xs md:text-sm font-medium leading-relaxed border-l-2 border-[#FFD200] pl-3 h-full",
                                theme.textSummary
                            )}>
                                {/* Adaptive line clamp for better fit */}
                                <span className="line-clamp-4 md:line-clamp-5 lg:line-clamp-6">
                                    {summary.summary_short}
                                </span>
                            </p>
                        </motion.div>
                    )}
                </div>

                {/* Bottom: Action / Tag */}
                <div className="p-4 relative z-10 flex items-center justify-between mt-auto">
                    <div className="flex items-center gap-2 transform translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 ease-out text-[#FFD200]">
                        <span className="text-[9px] font-black uppercase tracking-[0.2em]">Read Signal</span>
                        <ArrowRight size={12} className="stroke-[3px]" />
                    </div>
                </div>
            </motion.div>

            {/* EXPANDED FOCUS MODE - FULL PAGE DEEP NAVY */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        layoutId={cardId}
                        className={cn(
                            "fixed inset-0 z-[200] w-full h-full overflow-y-auto pointer-events-auto flex flex-col",
                            theme.bg
                        )}
                    >
                        {/* Sticky Header Action Bar */}
                        <div className="sticky top-0 right-0 left-0 p-6 flex justify-end gap-3 z-50 pointer-events-none bg-gradient-to-b from-[#004182] to-transparent">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsSaved(!isSaved);
                                }}
                                className={cn(
                                    "pointer-events-auto w-12 h-12 rounded-full flex items-center justify-center transition-all shadow-lg border",
                                    isSaved
                                        ? "bg-white text-[#004182] border-white"
                                        : "bg-[#004182] text-[#FFD200] border-[#FFD200]/30 hover:bg-white hover:text-[#004182]"
                                )}
                                title="Save for Later"
                            >
                                <Bookmark size={18} fill={isSaved ? "currentColor" : "none"} />
                            </button>

                            <button
                                onClick={handleClose}
                                className="pointer-events-auto px-6 h-12 rounded-full bg-white text-[#004182] font-black text-xs uppercase tracking-widest hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
                            >
                                <X size={16} />
                                <span>Close</span>
                            </button>
                        </div>

                        <div className="px-6 md:px-16 pb-16 pt-0 space-y-12 max-w-5xl mx-auto w-full text-white mt-8">
                            <motion.h2
                                layoutId={`${cardId}-title`}
                                className="text-4xl md:text-6xl lg:text-7xl font-black leading-[0.9] font-outfit uppercase tracking-tighter text-white"
                            >
                                {story.canonical_title}
                            </motion.h2>

                            {hasSummary && (
                                <div className="grid md:grid-cols-[1.5fr,1fr] gap-12">
                                    <div className="space-y-8">
                                        <p className="text-xl md:text-2xl font-bold leading-relaxed font-sans border-l-4 border-[#FFD200] pl-6 text-white/95">
                                            {summary.summary_short}
                                        </p>

                                        <div className="space-y-6">
                                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#FFD200]">Key Intelligence</h3>
                                            <div className="space-y-4">
                                                {summary.summary_bullets.map((bullet, idx) => (
                                                    <div key={idx} className="flex gap-4 group">
                                                        <div className="mt-2.5 w-1.5 h-1.5 rounded-full shrink-0 bg-[#FFD200]/60 transition-colors group-hover:bg-[#FFD200]" />
                                                        <span className="text-lg font-medium leading-snug text-white/90 group-hover:text-white transition-opacity">{bullet}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-8 pt-2">
                                        <div className="p-8 rounded-3xl bg-black/20 border border-[#FFD200]/10 space-y-6">
                                            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#FFD200]/50">Source Data</h3>
                                            <div className="grid gap-3">
                                                {story.items.map((item, i) => (
                                                    <a
                                                        key={i}
                                                        href={item.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="flex items-start justify-between p-4 rounded-xl bg-black/30 hover:bg-white text-[11px] font-bold text-white/80 hover:text-[#004182] transition-all border border-[#FFD200]/20 group/link"
                                                    >
                                                        <span className="line-clamp-2 leading-normal">{item.title}</span>
                                                        <ArrowUpRight size={12} className="shrink-0 ml-3 opacity-30 group-hover/link:opacity-100" />
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Additional details for full reading experience */}

                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
