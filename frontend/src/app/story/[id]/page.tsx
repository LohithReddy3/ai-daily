"use client";

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Share2, ArrowRight, ExternalLink, Calendar, Link as LinkIcon, X } from 'lucide-react';
import { Story } from '@/types';
import api from '@/lib/api';
import { cn, getCategoryGradient, getCategoryTheme, getCategoryIcon } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { useRouter, useParams, useSearchParams } from 'next/navigation';

export default function StoryPage() {
    const [story, setStory] = useState<Story | null>(null);
    const [loading, setLoading] = useState(true);
    const { user } = useAuth();
    const router = useRouter();
    const params = useParams();
    const searchParams = useSearchParams();
    const storyId = params?.id as string;

    const activePersona = (searchParams.get('persona') as string) || 'builders';

    useEffect(() => {
        if (storyId) {
            fetchStoryDetails();
        }
    }, [storyId]);

    const fetchStoryDetails = async () => {
        try {
            setLoading(true);
            const res = await api.get(`/stories/${storyId}`);
            setStory(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleBack = () => {
        router.back();
    };

    if (loading) {
        return (
            <div className="min-h-screen w-full bg-white flex flex-col items-center justify-center gap-4">
                <div className="w-10 h-10 rounded-full border-4 border-blue-600 border-t-transparent animate-spin" />
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Loading Intelligence...</span>
            </div>
        );
    }

    if (!story) {
        return (
            <div className="min-h-screen w-full bg-white flex flex-col items-center justify-center gap-4">
                <span className="text-gray-400">Story signal lost.</span>
                <button onClick={handleBack} className="text-blue-600 font-bold hover:underline">Return to Base</button>
            </div>
        );
    }

    const summary = story.summaries?.find(s => s.persona === activePersona) || story.summaries?.[0];
    const category = summary?.category || "Technology";
    const gradientColors = getCategoryGradient(category);
    const theme = getCategoryTheme(category);
    const CategoryIcon = getCategoryIcon(category);

    return (
        <div className="min-h-screen w-full bg-white font-sans selection:bg-blue-100 flex flex-col">

            {/* ROW 1: HEADER (scaled down 30%) */}
            <header className={cn("w-full py-14 px-6 md:px-12 flex flex-col items-center justify-center text-center relative bg-gradient-to-br min-h-[28vh]", gradientColors)}>
                {/* Back Button (Absolute Top Right) */}
                <button
                    onClick={handleBack}
                    className="absolute top-8 right-8 z-20 p-2 bg-white/20 hover:bg-white/40 rounded-full text-white transition-colors backdrop-blur-md"
                >
                    <X size={24} />
                </button>

                {/* Metadata (Absolute Top Left) */}
                <div className="absolute top-8 left-8 z-10 flex flex-col items-start gap-2">
                    <div className="flex items-center gap-3">
                        {story.items[0]?.source && (
                            <div className="px-2.5 py-1 bg-white/20 backdrop-blur-md rounded text-[11px] font-bold uppercase tracking-wider text-white border border-white/10">
                                {story.items[0].source.name}
                            </div>
                        )}
                        <span className="text-white/70 text-xs font-medium">
                            {new Date(story.created_at).toLocaleDateString(undefined, { month: 'long', day: 'numeric' })}
                        </span>
                    </div>
                </div>

                {/* Title (Center Stage) */}
                <div className="max-w-5xl mx-auto relative z-10 w-full px-4">
                    <h1 className="text-2xl md:text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight drop-shadow-sm">
                        {story.canonical_title}
                    </h1>
                </div>

                {/* Source Link (Absolute Bottom Right) */}
                <div className="absolute bottom-8 right-8 z-10">
                    {story.items[0] && (
                        <a
                            href={story.items[0].url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/80 hover:text-white transition-colors"
                        >
                            Read Full Source <ArrowRight size={12} />
                        </a>
                    )}
                </div>
            </header>

            {/* CONTENT BODY (Ultra-Tight Vertical Stack) */}
            <main className="flex-1 w-full px-4 md:px-8 py-4 flex flex-col gap-0">

                {/* ROW 2: IMPACT (was Why It Matters) - Ultra-Compact Block */}
                {summary && (
                    <section className={cn("w-full rounded-xl p-4 border transition-colors relative overflow-hidden mb-2", theme.bg, theme.border)}>
                        <div className="flex items-center gap-3 mb-2">
                            <div className={cn("p-2 rounded-lg bg-white/60 backdrop-blur-sm", theme.text)}>
                                <CategoryIcon size={28} strokeWidth={2.5} />
                            </div>
                            <span className={cn("text-sm font-black uppercase tracking-widest", theme.text)}>Impact</span>
                        </div>
                        <p className="text-lg md:text-xl text-gray-900 leading-relaxed font-bold">
                            {summary.summary_short.replace(/^(Why [Ii]t [Mm]atters:?\\s*)/i, "").trim()}
                        </p>
                    </section>
                )}

                {/* ROW 3: TAKEAWAYS (was Key Intelligence) - Ultra-Tight List */}
                {summary && summary.summary_bullets.length > 0 && (
                    <section className="w-full max-w-[98%] mx-auto mb-2">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-2">
                            <span className="w-4 h-[1px] bg-gray-200" /> Takeaways
                        </h3>
                        <ul className="space-y-1">
                            {summary.summary_bullets.map((bullet, i) => (
                                <li key={i} className="flex gap-2 items-start group">
                                    <div className={cn("w-2 h-2 rounded-full mt-2.5 shrink-0 transition-transform group-hover:scale-125 shadow-sm", theme.dot)} />
                                    <span className="text-lg md:text-xl text-gray-800 leading-relaxed font-medium">
                                        {bullet.split(/(\*\*.*?\*\*)/g).map((part, j) =>
                                            part.startsWith('**') && part.endsWith('**') ? (
                                                <strong key={j} className="text-gray-900 font-extrabold bg-blue-50/50 px-1 rounded">{part.slice(2, -2)}</strong>
                                            ) : part
                                        )}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {/* ROW 4: CONTEXT (was Deep Context) - Ultra-Compact Block */}
                {summary && summary.why_it_matters && (
                    <section className="w-full rounded-xl p-4 border bg-gray-50 border-gray-100 relative overflow-hidden">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Context</span>
                        </div>
                        <article className="prose prose-lg md:prose-xl prose-slate max-w-none prose-p:text-gray-600 prose-p:leading-relaxed prose-headings:text-gray-900 prose-headings:font-bold">
                            {summary.why_it_matters.split('\n').map((para, i) => (
                                para.length < 100 && !para.endsWith('.') && para.length > 0 ? (
                                    <h3 key={i} className="mt-8 mb-4">{para}</h3>
                                ) : para.length > 0 ? (
                                    <p key={i} className="mb-6">{para}</p>
                                ) : null
                            ))}
                        </article>
                    </section>
                )}

            </main>
        </div>
    );
}
