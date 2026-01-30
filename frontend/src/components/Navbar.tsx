"use client";
import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { LayoutDashboard, Compass, Bookmark, Settings, LogOut } from 'lucide-react';

export default function Navbar() {
    const pathname = usePathname();
    const { user, signOut, openAuthModal } = useAuth();

    const navItems = [
        { name: 'Brief', href: '/', icon: LayoutDashboard },
        { name: 'Explore', href: '/explore', icon: Compass },
        { name: 'Saved', href: '/saved', icon: Bookmark },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    return (
        <nav className="fixed top-0 left-0 w-64 h-full bg-zinc-950 border-r border-zinc-800 text-zinc-100 p-6 hidden md:flex flex-col">
            <div className="mb-10">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                    AI Daily
                </h1>
                <p className="text-xs text-zinc-500 mt-1">Intelligence for Humans</p>
            </div>

            <div className="flex-1 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                                isActive
                                    ? "bg-zinc-800/80 text-white shadow-lg shadow-black/20"
                                    : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                            )}
                        >
                            <Icon size={20} className={cn("transition-colors", isActive ? "text-blue-400" : "group-hover:text-blue-400")} />
                            <span className="font-medium">{item.name}</span>
                        </Link>
                    );
                })}
            </div>

            <div className="mt-auto pt-6 border-t border-zinc-800/50">
                {user ? (
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 px-2">
                            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold border border-blue-500/30">
                                {user.email?.[0].toUpperCase()}
                            </div>
                            <div className="overflow-hidden">
                                <p className="text-xs font-medium text-white truncate">{user.email}</p>
                                <p className="text-[10px] text-zinc-500">Free Plan</p>
                            </div>
                        </div>
                        <button
                            onClick={signOut}
                            className="flex items-center gap-3 px-4 py-2 text-zinc-500 hover:text-red-400 transition-colors w-full rounded-lg hover:bg-red-400/10"
                        >
                            <LogOut size={16} />
                            <span className="text-xs font-medium">Sign Out</span>
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => {
                            // alert("Debug: Sidebar Clicked"); 
                            openAuthModal();
                        }}
                        className="flex items-center gap-3 px-4 py-3 text-blue-400 bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 transition-all w-full rounded-xl"
                    >
                        <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                        <span className="text-sm font-bold">Sign In</span>
                    </button>
                )}
            </div>
        </nav>
    );
}
