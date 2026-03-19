export type Persona = 'builders' | 'executors' | 'explorers';

export interface Source {
    id: number;
    name: string;
    source_kind: string; // was type
    url: string;
    reputation_weight: number; // was trust_level
}

export interface Item {
    id: string;
    title: string;
    url: string;
    published_at: string;
    image_url?: string;
    source?: Source;
}

export interface StorySummary {
    id: string;
    persona: Persona;
    category?: string;
    summary_short: string;
    summary_bullets: string[];
    why_it_matters?: string;
    key_entities?: string[];
    confidence: string; // low, med, high
    supporting_urls: string[];
    insufficient_evidence: boolean;
}

export interface Story {
    id: string;
    canonical_title: string;
    signal_score: number; // was score
    confidence_score: number; // 0-1
    story_state: string;
    created_at: string;
    updated_at?: string;
    items: Item[];
    summaries: StorySummary[];
    related_stories?: RelatedStory[];
    is_saved?: boolean;
    generated_image_url?: string;
}

export interface RelatedStory {
    id: string;
    canonical_title: string;
    created_at: string;
    similarity_score: number;
}

export interface DailyBriefItem {
    story_id: string;
    title: string;
    summary: string;
    importance: string;
    signal_score: number;
    bullets: string[];
    urls: string[];
    why_it_matters?: string;
}

export interface DailyBrief {
    id: string;
    date: string;
    persona: Persona;
    items_json: DailyBriefItem[];
    generated_at: string;
}
