import React, { useMemo, useRef, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { ExternalLink } from 'lucide-react';

// Dynamically import ForceGraph2D as it uses window/canvas
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
    ssr: false,
    loading: () => <div className="w-full h-full bg-slate-950 animate-pulse" />
});

interface Trend {
    title: string;
    explanation: string;
    evidence: {
        id: string;
        title: string;
        url: string;
        signal_score: number;
        published_at: string;
        source: string;
    }[];
}

interface TrendsNetworkGraphProps {
    trends: Trend[];
}

// Simple Static Starfield Component
const Starfield = () => {
    // Generate MORE static stars for denser background
    const stars = useMemo(() => {
        return Array.from({ length: 300 }).map((_, i) => ({
            id: i,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            size: Math.random() * 2 + 0.5,
            opacity: Math.random() * 0.7 + 0.3,
            animationDuration: `${Math.random() * 3 + 2}s`
        }));
    }, []);

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {stars.map((star) => (
                <div
                    key={star.id}
                    className="absolute bg-white rounded-full animate-pulse"
                    style={{
                        top: star.top,
                        left: star.left,
                        width: `${star.size}px`,
                        height: `${star.size}px`,
                        opacity: star.opacity,
                        animationDuration: star.animationDuration
                    }}
                />
            ))}
        </div>
    );
};

const TrendsNetworkGraph = ({ trends }: TrendsNetworkGraphProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const fgRef = useRef<any>(null);

    // Start with 0/0 to prevent wrong initial render
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [hoverNode, setHoverNode] = useState<any>(null);
    const [universeItems, setUniverseItems] = useState<any[]>([]);

    // Start with 0/0 to prevent wrong initial render
    const [searchTerm, setSearchTerm] = useState('');
    const [filterSource, setFilterSource] = useState<string | null>(null);
    const [stats, setStats] = useState({ total: 0, visible: 0 });

    // Constants for Visual Strategy
    const SOURCE_COLORS: Record<string, string> = {
        'Research': '#10B981', // Emerald (Arxiv, OpenAI)
        'Tech': '#3B82F6',     // Blue (TechCrunch, Verge)
        'Business': '#F59E0B', // Amber (Bloomberg)
        'General': '#64748B'   // Slate (Others)
    };

    const getSourceCategory = (sourceName: string = ''): string => {
        const s = sourceName.toLowerCase();
        if (s.includes('arxiv') || s.includes('openai') || s.includes('deepmind') || s.includes('anthropic')) return 'Research';
        if (s.includes('techcrunch') || s.includes('verge') || s.includes('wired') || s.includes('venture')) return 'Tech';
        if (s.includes('bloomberg') || s.includes('reuters') || s.includes('wsj')) return 'Business';
        return 'General';
    };

    const getSourceColor = (sourceName: string) => SOURCE_COLORS[getSourceCategory(sourceName)] || SOURCE_COLORS['General'];

    useEffect(() => {
        if (!containerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                if (width > 0 && height > 0) {
                    setDimensions({ width, height });
                }
            }
        });

        resizeObserver.observe(containerRef.current);

        return () => resizeObserver.disconnect();
    }, []);

    // Fetch Universe Data (Background Stars)
    useEffect(() => {
        const fetchUniverse = async () => {
            try {
                // Fetch recent raw items for background "Noise"
                const res = await fetch('http://127.0.0.1:8000/trends/universe?limit=3600');
                if (res.ok) {
                    const data = await res.json();
                    setUniverseItems(data.items || []);
                }
            } catch (e) {
                console.error("Failed to fetch universe data", e);
            }
        };
        fetchUniverse();
    }, []);

    // Physics Configuration - DENSE CLUSTER + DATA UNIVERSE
    useEffect(() => {
        if (fgRef.current) {
            // Apply Dense Cluster Physics
            // We need enough repulsion to keep 500+ nodes from overlapping too much, 
            // but not so much they fly off screen.
            fgRef.current.d3Force('charge').strength((node: any) => {
                if (node.group === 'trend') return -100; // Trends repel strongly
                if (node.group === 'story') return -20;
                return -5; // Background items weak repulsion
            });

            fgRef.current.d3Force('link').distance(25);
            fgRef.current.d3Force('center').strength(0.6);

            // Re-heat simulation if trends/items update
            fgRef.current.d3ReheatSimulation();
        }
    }, [trends, universeItems]);

    const data = useMemo(() => {
        const nodes: any[] = [];
        const links: any[] = [];

        // 1. Add Universe Items (Background Data)
        // Render order: Background first
        // We now plot the true physics-based universe calculated by T-SNE 1536D reduction
        const clusterColors = [
            '#4B0082', '#00008B', '#006400', '#8B0000', '#FF8C00', '#FFD700',
            '#00CED1', '#FF69B4', '#8A2BE2', '#00FA9A', '#CD5C5C', '#4682B4', '#D2691E'
        ];

        universeItems.forEach((item) => {
            nodes.push({
                id: `item-${item.id}`,
                name: item.title,
                val: 1, // Tiny stars
                group: 'item',
                color: clusterColors[item.universe_cluster % clusterColors.length] || '#333333',
                url: item.url,
                source: item.source,
                fx: item.universe_x, // Pin X to precomputed T-SNE coordinate
                fy: item.universe_y  // Pin Y to precomputed T-SNE coordinate
            });
        });

        if (!trends) return { nodes, links };

        // 2. Add Trends & Stories
        trends.forEach((trend, idx) => {
            const trendId = `trend-${idx}`;
            nodes.push({
                id: trendId,
                name: trend.title,
                val: 35, // Big planets
                group: 'trend',
                color: '#3B82F6', // Default Blue Planet
                isTrend: true
            });

            trend.evidence.forEach((story) => {
                const storyId = `story-${story.id}`;
                if (!nodes.find(n => n.id === storyId)) {
                    nodes.push({
                        id: storyId,
                        name: story.title,
                        val: 4, // Visible stars
                        group: 'story',
                        color: '#FFFFFF', // White stars
                        url: story.url,
                        source: story.source // Pass source for tooltip
                    });
                }
                links.push({ source: trendId, target: storyId });
            });
        });

        return { nodes, links };
    }, [trends, universeItems]);

    // Update Stats when filters change
    useEffect(() => {
        if (!data.nodes.length) return;

        const total = data.nodes.length;
        // Calculate visible count based on filters
        const visible = data.nodes.filter(n => {
            const matchesSearch = !searchTerm || n.name.toLowerCase().includes(searchTerm.toLowerCase()) || (n.source && n.source.toLowerCase().includes(searchTerm.toLowerCase()));
            const matchesSource = !filterSource || (n.source && getSourceCategory(n.source) === filterSource);
            return matchesSearch && matchesSource;
        }).length;

        setStats({ total, visible });
    }, [data, searchTerm, filterSource]);

    // Helper to check if node is connected to hoverNode
    const isConnected = (node: any) => {
        if (!hoverNode) return false;
        if (hoverNode === node) return true;
        // If hovering a Trend, highlight its stories
        if (hoverNode.group === 'trend' && node.group === 'story') {
            // Find link
            const link = data.links.find(l => (l.source.id === hoverNode.id && l.target.id === node.id) || (l.source.id === node.id && l.target.id === hoverNode.id));
            return !!link;
        }
        return false;
    }

    return (
        <div ref={containerRef} className="absolute inset-0 bg-slate-950 rounded-b-xl overflow-hidden shadow-inner z-0 border-t border-slate-900 group">
            {/* Starry Background Effect (CSS Radial + Static Stars) */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-[#020617] to-black opacity-80 pointer-events-none" />
            <Starfield />

            {/* HUD: Universe Controls */}
            <div className="absolute top-4 right-4 z-10 flex flex-col gap-2 w-64 transition-opacity duration-300 opacity-0 group-hover:opacity-100">
                <input
                    type="text"
                    placeholder="Search Universe..."
                    className="w-full bg-slate-900/80 backdrop-blur border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />

                <div className="flex gap-1 flex-wrap">
                    {['Research', 'Tech', 'Business', 'General'].map(cat => (
                        <button
                            key={cat}
                            onClick={() => setFilterSource(filterSource === cat ? null : cat)}
                            className={`px-2 py-1 rounded text-[10px] uppercase font-medium border transition-colors ${filterSource === cat
                                ? `bg-${cat === 'Research' ? 'emerald' : cat === 'Tech' ? 'blue' : cat === 'Business' ? 'amber' : 'slate'}-500/20 border-${cat === 'Research' ? 'emerald' : cat === 'Tech' ? 'blue' : cat === 'Business' ? 'amber' : 'slate'}-500 text-white`
                                : 'bg-black/40 border-slate-800 text-slate-400 hover:border-slate-600'
                                }`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {dimensions.width > 0 && (
                <ForceGraph2D
                    ref={fgRef}
                    width={dimensions.width}
                    height={dimensions.height}
                    graphData={data}
                    nodeRelSize={6}
                    linkColor={(link: any) => {
                        // Check if link connects filtered-out nodes?
                        // For now keep link logic simple, mostly visual fade handled in nodeCanvasObject
                        if (hoverNode && (link.source === hoverNode || link.target === hoverNode)) {
                            return 'rgba(255, 255, 255, 0.5)';
                        }
                        return 'rgba(255, 255, 255, 0.1)'; // Dim default
                    }}
                    onNodeHover={setHoverNode}
                    nodeLabel={(node: any) => `<div style="background: rgba(0,0,0,0.8); padding: 4px 8px; border-radius: 4px; font-size: 12px; color: white; border: 1px solid rgba(255,255,255,0.2);">${node.source ? `[${node.source}] ` : ''}${node.name}</div>`}
                    onNodeClick={(node: any) => {
                        // If planet, maybe zoom in? currently just open link if url
                        if (node.url) {
                            window.open(node.url, '_blank');
                        }
                    }}
                    nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                        const label = node.name;
                        const fontSize = 12 / globalScale;
                        ctx.font = `${fontSize}px Sans-Serif`;

                        const isHovered = hoverNode === node;
                        const isRelated = isConnected(node);

                        // FILTER LOGIC
                        let isMatched = true;
                        if (searchTerm) {
                            isMatched = node.name.toLowerCase().includes(searchTerm.toLowerCase()) || (node.source && node.source.toLowerCase().includes(searchTerm.toLowerCase()));
                        }
                        if (filterSource && isMatched) {
                            isMatched = node.source && getSourceCategory(node.source) === filterSource;
                            // Always show trends? yes
                            if (node.group === 'trend') isMatched = true;
                        }

                        // Determine Visibility
                        const isDimmed = (hoverNode && !isHovered && !isRelated) || (!isMatched && searchTerm);

                        if (isDimmed) {
                            ctx.globalAlpha = 0.1; // Fade out non-matches deeply
                        } else {
                            ctx.globalAlpha = 1.0;
                        }

                        if (node.group === 'trend') {
                            // Draw Planet (Glowing)
                            const radius = 5;

                            // Glow if hovered or related
                            if (isHovered || isRelated) {
                                ctx.shadowBlur = 30;
                                ctx.shadowColor = node.color;
                            } else {
                                ctx.shadowBlur = 20;
                                ctx.shadowColor = node.color;
                            }

                            ctx.beginPath();
                            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                            ctx.fillStyle = node.color;
                            ctx.fill();
                            ctx.shadowBlur = 0;

                            if ((globalScale > 0.6 || isHovered || isRelated) && isMatched) {
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'top';
                                ctx.fillStyle = isHovered ? '#FFFFFF' : 'rgba(255, 255, 255, 0.9)';
                                ctx.fillText(label, node.x, node.y + radius + 4);
                            }
                        } else if (node.group === 'story') {
                            // Draw Story Star (White)
                            const radius = 1.5;

                            // Shine if related to hovered planet
                            if (isRelated) {
                                ctx.shadowBlur = 10;
                                ctx.shadowColor = '#FFFFFF';
                            }

                            ctx.beginPath();
                            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                            ctx.fillStyle = isHovered || isRelated ? '#FFFFFF' : 'rgba(255, 255, 255, 0.8)';
                            ctx.fill();
                            ctx.shadowBlur = 0;

                            if (isHovered && isMatched) {
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'top';
                                ctx.fillStyle = '#FFFFFF';
                                // Show Source if available? Stories usually don't have source field in this node obj yet, check data mapping
                                ctx.fillText(label, node.x, node.y + radius + 2);
                            }
                        } else if (node.group === 'item') {
                            // Draw Background Data Star (Dim, Tiny)
                            const radius = 0.8 + (isMatched && searchTerm ? 1 : 0); // Grow if matched

                            ctx.beginPath();
                            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                            // Highlight match if search active
                            ctx.fillStyle = (isMatched && searchTerm) ? '#FFFFFF' : (isHovered ? '#FFFFFF' : node.color);
                            ctx.fill();

                            if (isHovered && isMatched) {
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'bottom';
                                ctx.fillStyle = '#E2E8F0';
                                // Show Source + Title
                                const text = node.source ? `[${node.source}] ${label}` : label;

                                // Draw a solid dark background for the text so it pops against the stars
                                const textWidth = ctx.measureText(text).width;
                                const padX = 8 / globalScale;
                                const padY = 4 / globalScale;
                                const bWidth = textWidth + (padX * 2);
                                const bHeight = fontSize + (padY * 2);

                                ctx.fillStyle = 'rgba(0,0,0,0.85)';
                                ctx.beginPath();
                                ctx.roundRect(node.x - bWidth / 2, node.y - radius - (4 / globalScale) - bHeight, bWidth, bHeight, 4 / globalScale);
                                ctx.fill();

                                ctx.fillStyle = '#FFFFFF';
                                ctx.fillText(text, node.x, node.y - radius - (4 / globalScale) - padY);
                            }
                        }
                        ctx.globalAlpha = 1.0; // Reset
                    }}
                    nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
                        const radius = node.group === 'trend' ? 6 : (node.group === 'item' ? 3 : 3); // Larger hit area for items
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                        ctx.fillStyle = color;
                        ctx.fill();
                    }}
                    warmupTicks={50}
                    cooldownTicks={100}
                    onEngineStop={() => {
                        fgRef.current?.zoomToFit(200, 20);
                    }}
                    d3AlphaDecay={0.02}
                    d3VelocityDecay={0.4}
                />
            )}

            {/* Cosmos Map Legend & Stats */}
            <div className="absolute top-4 left-4 flex flex-col gap-2 pointer-events-none transition-opacity duration-500" style={{ opacity: searchTerm ? 0.5 : 1 }}>
                <div className="bg-black/60 p-3 rounded-2xl text-xs text-slate-300 backdrop-blur-md border border-white/10 shadow-lg">
                    <p className="font-medium mb-2 text-white tracking-wide uppercase text-[10px]">Data Universe</p>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></span>
                        <span>Trends ({trends?.length || 0})</span>
                    </div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_4px_rgba(255,255,255,0.8)]"></span>
                        <span>Evidence ({data.nodes.filter(n => n.group === 'story').length})</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex gap-0.5">
                            <span className="w-1 h-1 rounded-full bg-emerald-500"></span>
                            <span className="w-1 h-1 rounded-full bg-blue-500"></span>
                            <span className="w-1 h-1 rounded-full bg-amber-500"></span>
                        </div>
                        <span>Raw Data ({universeItems.length})</span>
                    </div>
                </div>

                <div className="bg-blue-950/40 p-2 rounded-xl text-[10px] text-blue-200 backdrop-blur-md border border-blue-500/20 shadow-lg">
                    <p>Scanning <strong>{stats.visible}</strong> / {stats.total} signals</p>
                </div>
            </div>
        </div>
    );
};

export default TrendsNetworkGraph;
