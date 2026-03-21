import { api } from './api';

export interface LeaderboardUser {
    id: string;
    username: string;
    avatar_url?: string;
    roi: number;
    win_rate: number;
    global_score?: number;
}

export interface UserProfile {
    id: string;
    username: string;
    email?: string;
    avatar_url?: string;
    bio?: string;
    follower_count: number;
    is_followed_by_me: boolean;
    is_tipster: boolean;
    subscription_price?: string;
    halo_color?: string;
    stats?: {
        roi: number;
        win_rate: number;
        total_bets: number;
        total_profit?: number;
    };
    sport_stats?: Array<{
        sport: string;
        total_bets: number;
        wins: number;
        winrate: number;
        roi: number;
    }>;
    badges?: Array<{
        badge_name: string;
        description: string;
        awarded_at: string | null;
    }>;
}

/**
 * Fetch the top 50 users sorted by ROI
 */
export const fetchLeaderboard = async (): Promise<LeaderboardUser[]> => {
    const { data } = await api.get('/api/users/leaderboard/');
    return data;
};

/**
 * Search users by username
 * @param query - Search query string
 */
export const searchUsers = async (query: string): Promise<LeaderboardUser[]> => {
    if (!query || query.trim() === '') return [];

    const { data } = await api.get(`/api/users/?search=${encodeURIComponent(query)}`);

    // Handle both paginated response { results: [...] } and direct array
    if (data.results) {
        return data.results;
    }
    return data;
};

/**
 * Fetch public profile of a specific user
 * @param id - User ID
 */
export const fetchUserProfile = async (id: string): Promise<UserProfile> => {
    const { data } = await api.get(`/api/users/${id}/`);
    return data;
};

/**
 * Fetch bets posted by a specific user
 * @param id - User ID (author)
 */
export const fetchUserBets = async (id: string) => {
    const { data } = await api.get(`/api/bets/?author=${id}`);
    return data;
};
