import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, ZAxis, Cell } from 'recharts';

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

interface TrendsTimelineProps {
    trends: Trend[];
}

const TrendsTimeline = ({ trends }: TrendsTimelineProps) => {
    const data = trends.flatMap((trend, idx) =>
        trend.evidence.map(story => ({
            ...story,
            trendTitle: trend.title,
            trendIndex: idx,
            timestamp: new Date(story.published_at).getTime(),
            dateStr: new Date(story.published_at).toLocaleDateString()
        }))
    );

    // Sort by time
    data.sort((a, b) => a.timestamp - b.timestamp);

    const colors = ['#2563EB', '#059669', '#D97706', '#DC2626', '#7C3AED']; // Blue, Green, Amber, Red, Violet

    return (
        <div className="w-full h-[600px] bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-6">Timeline Analysis</h3>
            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                        type="number"
                        dataKey="timestamp"
                        name="Time"
                        domain={['auto', 'auto']}
                        tickFormatter={(unixTime) => new Date(unixTime).toLocaleDateString()}
                        stroke="#94a3b8"
                        fontSize={10}
                    />
                    <YAxis
                        type="number"
                        dataKey="signal_score"
                        name="Signal Score"
                        unit=""
                        stroke="#94a3b8"
                        fontSize={10}
                        label={{ value: 'Signal Score', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }}
                    />
                    <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                const item = payload[0].payload;
                                return (
                                    <div className="bg-white p-3 border border-gray-200 shadow-lg rounded-lg text-xs max-w-xs">
                                        <p className="font-bold text-gray-900 mb-1">{item.title}</p>
                                        <p className="text-gray-500 mb-1">{item.dateStr}</p>
                                        <div className="flex items-center gap-1 mt-2 pt-2 border-t border-gray-100">
                                            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[item.trendIndex % colors.length] }} />
                                            <span className="text-gray-600 font-medium">{item.trendTitle}</span>
                                        </div>
                                    </div>
                                );
                            }
                            return null;
                        }}
                    />
                    <Scatter name="Stories" data={data} fill="#8884d8">
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={colors[entry.trendIndex % colors.length]} />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TrendsTimeline;
