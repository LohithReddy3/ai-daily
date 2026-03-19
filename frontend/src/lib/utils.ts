import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Zap, Target, TrendingUp, Cpu, Shield, Briefcase, Layers } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function stringToColor(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const c = (hash & 0x00ffffff).toString(16).toUpperCase();
    return '#' + '00000'.substring(0, 6 - c.length) + c;
}

export function generateGradient(id: string): string {
    // "Golden Sunrise" - Amber yellow to deep orange
    // Warm, vibrant, artistic sunrise aesthetic
    // Previous: "Midnight Sapphire" #1E3A8A,#334155 | "Emerald Dusk" #047857,#374151
    return `#F59E0B, #EA580C`;
}

// ------------------------------------------------------------------
// CATEGORY HELPERS (Shared Logic)
// ------------------------------------------------------------------

export const getCategoryGradient = (category: string) => {
    const cat = (category || "").toLowerCase();
    if (cat.includes('model') || cat.includes('llm')) return 'from-blue-600 to-indigo-600';
    if (cat.includes('rag') || cat.includes('agent')) return 'from-emerald-500 to-teal-600';
    if (cat.includes('compute') || cat.includes('hardware')) return 'from-orange-500 to-red-600';
    if (cat.includes('business') || cat.includes('enterprise')) return 'from-slate-700 to-gray-900';
    if (cat.includes('demo') || cat.includes('creative')) return 'from-pink-500 to-rose-600';
    if (cat.includes('policy') || cat.includes('safety')) return 'from-amber-400 to-orange-500';
    return 'from-blue-500 to-cyan-500'; // Default
};

export const getCategoryTheme = (category: string) => {
    const cat = (category || "").toLowerCase();
    // Returns: { text, bg, border, icon }
    if (cat.includes('model')) return { text: 'text-blue-700', bg: 'bg-blue-50/80', border: 'border-blue-100', icon: 'text-blue-600', dot: 'bg-blue-500' };
    if (cat.includes('agent')) return { text: 'text-emerald-800', bg: 'bg-emerald-50/80', border: 'border-emerald-100', icon: 'text-emerald-600', dot: 'bg-emerald-500' };
    if (cat.includes('compute')) return { text: 'text-orange-800', bg: 'bg-orange-50/80', border: 'border-orange-100', icon: 'text-orange-600', dot: 'bg-orange-500' };
    if (cat.includes('business')) return { text: 'text-slate-800', bg: 'bg-slate-50/80', border: 'border-slate-200', icon: 'text-slate-600', dot: 'bg-slate-500' };
    if (cat.includes('policy')) return { text: 'text-amber-800', bg: 'bg-amber-50/80', border: 'border-amber-100', icon: 'text-amber-600', dot: 'bg-amber-500' };
    return { text: 'text-gray-800', bg: 'bg-gray-50', border: 'border-gray-100', icon: 'text-gray-500', dot: 'bg-gray-500' };
};

export const getCategoryIcon = (category: string) => {
    const cat = (category || "").toLowerCase();
    if (cat.includes('model')) return Layers;
    if (cat.includes('agent')) return Target;
    if (cat.includes('compute')) return Cpu;
    if (cat.includes('business')) return Briefcase;
    if (cat.includes('policy')) return Shield;
    return Zap;
}
