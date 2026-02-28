import { api } from './api';

export const toggleLike = async (betId: string) => {
    const { data } = await api.post(`/api/social/likes/${betId}/toggle/`);
    return data; // { liked: boolean }
};

export const fetchComments = async (betId: string) => {
    const { data } = await api.get(`/api/social/comments/?bet_id=${betId}`);
    return data;
};

export const postComment = async (betId: string, content: string) => {
    const { data } = await api.post('/api/social/comments/', { bet: betId, content });
    return data;
};

/**
 * Toggle follow status for a user
 * @param userId - ID of the user to follow/unfollow
 * @returns { following: boolean }
 */
export const toggleFollow = async (userId: string) => {
    const { data } = await api.post(`/api/social/follow/${userId}/toggle/`);
    return data;
};
