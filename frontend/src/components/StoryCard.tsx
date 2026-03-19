"use client";
import React, { useState } from 'react';
import { Story, Persona } from '@/types';
import { cn, generateGradient, getCategoryGradient, getCategoryIcon } from '@/lib/utils';
import { Bookmark, X, ArrowRight, Zap, Target, TrendingUp, Cpu, Shield, Briefcase, Layers } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';

import { useAuth } from '@/context/AuthContext';
import api from '@/lib/api';

interface StoryCardProps {
    story: Story;
    activePersona: Persona;
    layoutId?: string;
    index?: number;
}



export default function StoryCard({ story, activePersona, layoutId, index = 0 }: StoryCardProps) {
    const { user, openAuthModal } = useAuth();
    const [isSaved, setIsSaved] = useState(story.is_saved || false);

    // Smart Fallback Generation
    const summary = story.summaries?.find(s => s.persona === activePersona) || story.summaries?.[0];
    const category = summary?.category || "Technology";
    const seed = story.id;
    // Use a high-quality abstract tech prompt
    const fallbackUrl = `https://image.pollinations.ai/prompt/abstract%20futuristic%20tech%20art%20${encodeURIComponent(category)}%20minimalist%20wallpaper?width=800&height=450&seed=${seed}&nologo=true`;

    // Primary: Custom Gen -> Scraped -> Smart Fallback
    const primaryUrl = story.generated_image_url || story.items[0]?.image_url || fallbackUrl;

    const [imgSrc, setImgSrc] = useState(primaryUrl);

    // Update if prop changes
    React.useEffect(() => {
        setImgSrc(story.generated_image_url || story.items[0]?.image_url || fallbackUrl);
    }, [story]);

    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();

    // Sync state with prop if it changes (e.g. after refetch)
    React.useEffect(() => {
        setIsSaved(story.is_saved || false);
    }, [story.is_saved]);

    // Check if this card is expanded based on URL
    const isExpanded = searchParams.get('story') === story.id;

    // Handle expansion via URL -> Dedicated Page
    const handleExpand = () => {
        router.push(`/story/${story.id}`);
    };

    // Handle close via URL (back)
    const handleClose = (e?: React.MouseEvent) => {
        e?.stopPropagation();
        router.back();
    };

    const handleSave = async (e: React.MouseEvent) => {
        e.stopPropagation();

        if (!user) {
            openAuthModal();
            return;
        }

        // Optimistic Update
        const previousState = isSaved;
        setIsSaved(!isSaved);

        try {
            if (!previousState) {
                // Save
                await api.post(`/stories/${story.id}/save`);
                console.log('Story saved successfully');
            } else {
                // Unsave
                await api.delete(`/stories/${story.id}/save`);
                console.log('Story removed successfully');
            }
        } catch (error) {
            console.error('Failed to save story:', error);
            // Revert on error
            setIsSaved(previousState);
            alert("Error saving story. Please check console.");
        }
    };

    const gradientColors = getCategoryGradient(category);
    const CategoryIcon = getCategoryIcon(category);

    const hasSummary = !!summary;
    const date = new Date(story.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    // Use a unique ID for layout animations
    const cardId = layoutId || `story-${story.id}`;

    return (
        <motion.div
            layoutId={cardId}
            transition={{ delay: index * 0.05 }}
            onClick={handleExpand}
            className={cn(
                "relative group cursor-pointer w-full h-full min-h-[320px] md:min-h-0 overflow-hidden hover:z-10",
                "bg-white hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1",
                "flex flex-col justify-between border border-gray-100/50"
            )}
        >
            {/* Top Half: CATEGORY GRADIENT HEADER */}
            <div className={cn("relative w-full min-h-[120px] shrink-0 p-5 flex flex-col justify-between bg-gradient-to-br", gradientColors)}>
                {/* Texture/Noise overlay if desired, for now clean gradient */}

                {/* Top Row: Date & Source */}
                <div className="flex justify-between items-start text-white/80 text-[10px] font-bold uppercase tracking-widest">
                    <span>{story.items[0]?.source?.name || "Source"}</span>
                    <span className="opacity-70">{date}</span>
                </div>

                {/* Title */}
                <h2 className="relative z-10 text-base md:text-lg font-black leading-tight text-white mt-1 drop-shadow-sm line-clamp-3">
                    {story.canonical_title}
                </h2>
            </div>

            {/* Bottom Half: CONTENT */}
            <div className="flex-1 p-5 flex flex-col justify-between bg-white relative">

                {/* IMPACT SECTION */}
                <div className="flex flex-col gap-3">
                    {hasSummary ? (
                        <div className="relative">
                            {/* Impact Label */}
                            <div className="flex items-center gap-2 mb-2 text-blue-600/80">
                                <CategoryIcon size={12} strokeWidth={3} />
                                <span className="text-[9px] font-black uppercase tracking-widest">Impact</span>
                            </div>

                            {/* Summary Text (Cleaned) */}
                            <p className="text-sm text-gray-700 leading-relaxed font-medium line-clamp-4">
                                {summary.summary_short.replace(/^(Why [Ii]t [Mm]atters:?\s*)/i, "").trim()}
                            </p>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 text-gray-300 animate-pulse">
                            <div className="h-2 w-2 rounded-full bg-gray-300" />
                            <span className="text-[10px] uppercase font-bold tracking-widest">Processing...</span>
                        </div>
                    )}
                </div>

                {/* Footer: DEEP DIVE ACTION */}
                <div className="mt-4 pt-4 border-t border-gray-50 flex items-center justify-between">
                    {/* Category Label */}
                    <span className="text-[9px] font-bold uppercase tracking-widest text-gray-400 group-hover:text-blue-500 transition-colors">
                        {category}
                    </span>

                    {/* Action Button */}
                    <div className="flex items-center gap-2 group/btn">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-300 group-hover/btn:text-black transition-colors">
                            Deep Dive
                        </span>
                        <div className="w-6 h-6 rounded-full bg-gray-50 group-hover/btn:bg-black group-hover/btn:text-white flex items-center justify-center transition-all">
                            <ArrowRight size={12} strokeWidth={2.5} />
                        </div>
                    </div>
                </div>
            </div>

        </motion.div >
    );
}
