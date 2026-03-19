
import React, { useEffect, useState } from 'react';
import { getTrends } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Loader2, Link, Network, Activity, BarChart3, FileText } from 'lucide-react';
import TrendsNetworkGraph from './TrendsNetworkGraph';
import TrendsTimeline from './TrendsTimeline';
import TrendsImpactMap from './TrendsImpactMap';

interface Trend {
    title: string;
    explanation: string;
    evidence_story_ids: string[];
    evidence_titles: string[];
    evidence: {
        id: string;
        title: string;
        url: string;
        signal_score: number;
        published_at: string;
        source: string;
    }[];
}

type ViewMode = 'briefing' | 'network' | 'timeline' | 'impact';

const TrendsView = () => {
    const [days, setDays] = useState(7);
    const [viewMode, setViewMode] = useState<ViewMode>('briefing');
    const [trends, setTrends] = useState<Trend[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

    useEffect(() => {
        fetchTrends();
    }, [days]);

    const fetchTrends = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getTrends(days);
            setTrends(data);
        } catch (err) {
            setError("Failed to load trends. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    // Helper to assign a specific color theme based on the trend content
    const getTrendColor = (trend: Trend) => {
        const text = (trend.title + " " + trend.explanation).toLowerCase();

        if (text.includes('agent') || text.includes('autonomous') || text.includes('rag')) return 'bg-emerald-500';
        if (text.includes('compute') || text.includes('chip') || text.includes('nvidia') || text.includes('hardware')) return 'bg-orange-500';
        if (text.includes('policy') || text.includes('safety') || text.includes('regulation') || text.includes('ethics')) return 'bg-amber-500';
        if (text.includes('business') || text.includes('investment') || text.includes('funding') || text.includes('startup')) return 'bg-slate-700';
        if (text.includes('image') || text.includes('video') || text.includes('audio') || text.includes('creative')) return 'bg-pink-500';

        // Default to Model/LLM
        return 'bg-blue-600';
    };

    const renderContent = () => {
        if (loading) {
            return (
                <div className="flex flex-col items-center justify-center py-24 space-y-4">
                    <Loader2 className="animate-spin text-gray-300" size={32} />
                    <p className="text-xs text-gray-400 font-mono uppercase tracking-widest">Synthesizing intelligence...</p>
                </div>
            );
        }

        if (error) {
            return <div className="p-4 bg-red-50 text-red-600 text-sm rounded border border-red-100">{error}</div>;
        }

        if (trends.length === 0) {
            return <p className="text-gray-400 text-center italic py-24">No significant trends detected in this window.</p>;
        }

        switch (viewMode) {
            case 'network':
                return <TrendsNetworkGraph trends={trends} />;
            case 'timeline':
                return <TrendsTimeline trends={trends} />;
            case 'impact':
                return <TrendsImpactMap trends={trends} />;
            case 'briefing':
            default:
                return (
                    <ul className="space-y-12">
                        {trends.map((trend, idx) => {
                            const bulletColor = getTrendColor(trend);
                            const isExpanded = expandedIndex === idx;

                            return (
                                <li key={idx} className="relative group grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-x-12 gap-y-4 items-start border-b border-dashed border-gray-100 pb-10 last:border-0">
                                    {/* Bullet Marker */}
                                    <div className={cn("absolute -left-6 top-3 w-2.5 h-2.5 rounded-full", bulletColor)} />

                                    <div className="flex flex-col gap-3">
                                        <h3 className="text-2xl md:text-3xl font-medium text-gray-900 leading-tight font-serif group-hover:text-blue-700 transition-colors">
                                            {trend.title}
                                        </h3>
                                        <p className="text-gray-600 leading-relaxed text-lg font-sans max-w-5xl">
                                            {trend.explanation}
                                        </p>
                                    </div>

                                    <div className="flex flex-col items-start lg:items-end gap-3 mt-1">
                                        <button
                                            onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                                            className={cn(
                                                "inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wide border transition-all",
                                                isExpanded
                                                    ? "bg-gray-900 text-white border-gray-900"
                                                    : "bg-white text-gray-500 border-gray-200 hover:border-gray-900 hover:text-gray-900"
                                            )}
                                        >
                                            <Link size={12} />
                                            Sources [{trend.evidence_titles.length}]
                                            {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                        </button>

                                        <AnimatePresence>
                                            {isExpanded && (
                                                <motion.div
                                                    initial={{ height: 0, opacity: 0 }}
                                                    animate={{ height: "auto", opacity: 1 }}
                                                    exit={{ height: 0, opacity: 0 }}
                                                    className="w-full lg:text-right overflow-hidden"
                                                >
                                                    <ul className="mt-2 space-y-2 py-1">
                                                        {trend.evidence_titles.map((title, i) => (
                                                            <li key={i} className="text-[11px] text-gray-500 hover:text-blue-600 cursor-pointer transition-colors leading-normal border-b border-gray-50 pb-1 last:border-0">
                                                                {title}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                );
        }
    };

    return (
        <div className="w-full h-full flex flex-col items-center overflow-y-auto bg-[#F9FAFB] p-4 md:p-6">
            {/* Document Container: Full Width, Growing Height */}
            <div className="w-full max-w-[1800px] bg-white shadow-xl border border-gray-200 h-full flex flex-col px-4 py-6 relative flex-shrink-0">

                {/* Header Section */}
                <div className="border-b border-gray-100 mb-2 gap-4 flex-shrink-0">
                    <div className="flex flex-col md:flex-row md:items-end justify-between pb-4">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400">
                                    Intelligence Briefing
                                </span>
                                <span className="px-2 py-0.5 rounded bg-gray-100 text-[10px] font-mono text-gray-500">
                                    {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                </span>
                            </div>
                            <h1 className="text-3xl md:text-4xl font-serif font-medium tracking-tight text-gray-900">
                                Market Trends
                            </h1>
                        </div>

                        {/* Window Selector */}
                        <div className="flex items-center gap-1 bg-gray-50/50 p-1 rounded-lg">
                            {[7, 15, 30, 90].map((d) => (
                                <button
                                    key={d}
                                    onClick={() => setDays(d)}
                                    className={cn(
                                        "px-3 py-1 text-[10px] font-bold uppercase tracking-wide rounded-md transition-all",
                                        days === d
                                            ? "bg-white text-black shadow-sm border border-gray-100"
                                            : "text-gray-400 hover:text-black"
                                    )}
                                >
                                    {d}D
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Visual Mode Tabs */}
                    <div className="flex items-center gap-6 -mb-px">
                        {[
                            { id: 'briefing', label: 'Briefing', icon: FileText },
                            { id: 'network', label: 'Network', icon: Network },
                            { id: 'timeline', label: 'Timeline', icon: Activity },
                            { id: 'impact', label: 'Impact', icon: BarChart3 },
                        ].map((tab) => {
                            const Icon = tab.icon;
                            const isActive = viewMode === tab.id;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setViewMode(tab.id as ViewMode)}
                                    className={cn(
                                        "flex items-center gap-2 pb-3 text-[11px] font-bold uppercase tracking-wider border-b-2 transition-colors",
                                        isActive
                                            ? "border-blue-600 text-blue-600"
                                            : "border-transparent text-gray-400 hover:text-gray-600 hover:border-gray-200"
                                    )}
                                >
                                    <Icon size={14} />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Content */}
                <div className={cn(
                    "flex-1 relative",
                    viewMode === 'briefing' ? "overflow-auto p-4" : "overflow-hidden h-full"
                )}>
                    {renderContent()}
                </div>
            </div>
        </div>
    );
};

export default TrendsView;
