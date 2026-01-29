export type Persona = 'builders' | 'executors' | 'explorers' | 'thought_leaders';

export interface Source {
    id: number;
    name: string;
    type: string;
    url: string;
    trust_level: string;
}

export interface Item {
    id: string;
    title: string;
    url: string;
    published_at: string;
}

export interface StorySummary {
    id: string;
    persona: Persona;
    category?: string;
    summary_short: string;
    summary_bullets: string[];
    why_it_matters?: string;
    key_entities?: string[]; // Used for open_questions or actionable_steps
    confidence: string;
}

export interface Story {
    id: string;
    canonical_title: string;
    score: number;
    tags: string[];
    created_at: string;
    items: Item[];
    summaries: StorySummary[];
    is_saved?: boolean;
}
