import React from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';

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

interface TrendsImpactMapProps {
    trends: Trend[];
}

const TrendsImpactMap = ({ trends }: TrendsImpactMapProps) => {
    // Calculate total impact (sum of signal scores or count of stories)
    const data = trends.map((trend, idx) => ({
        name: trend.title,
        size: trend.evidence.reduce((sum, story) => sum + story.signal_score, 0),
        storyCount: trend.evidence.length,
        fill: ['#2563EB', '#059669', '#D97706', '#DC2626', '#7C3AED'][idx % 5]
    }));

    // Sort by size
    data.sort((a, b) => b.size - a.size);

    return (
        <div className="w-full h-[600px] bg-white rounded-xl border border-gray-100 p-6 shadow-sm overflow-hidden">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-6">Impact Heatmap</h3>
            <div className="w-full h-full relative">
                <ResponsiveContainer width="100%" height="90%">
                    <Treemap
                        data={data}
                        dataKey="size"
                        stroke="#fff"
                        fill="#8884d8"
                        content={<CustomizedContent colors={data.map(d => d.fill)} />}
                    >
                        <Tooltip content={<CustomTooltip />} />
                    </Treemap>
                </ResponsiveContainer>
                <div className="absolute top-0 right-0 text-xs text-gray-400">
                    *Size = Total Signal Score
                </div>
            </div>
        </div>
    );
};

const CustomizedContent = (props: any) => {
    const { root, depth, x, y, width, height, index, colors, name, value } = props;

    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: colors[index % colors.length],
                    stroke: '#fff',
                    strokeWidth: 2 / (depth + 1e-10),
                    strokeOpacity: 1 / (depth + 1e-10),
                }}
            />
            {width > 50 && height > 50 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={Math.min(width / 10, 14)}
                    fontWeight="bold"
                >
                    {name.split(' ').slice(0, 2).join(' ')}...
                </text>
            )}
            {width > 50 && height > 50 && (
                <text
                    x={x + width / 2}
                    y={y + height / 2 + 16}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize={10}
                >
                    {value} Signal
                </text>
            )}
        </g>
    );
};

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-white p-3 border border-gray-200 shadow-lg rounded-lg text-xs">
                <p className="font-bold text-gray-900">{data.name}</p>
                <p className="text-gray-500">Total Signal Impact: {data.size}</p>
                <p className="text-gray-500">Stories: {data.storyCount}</p>
            </div>
        );
    }
    return null;
};

export default TrendsImpactMap;
