
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

// Types for API responses
interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

export const clearTokens = () => {
    if (typeof window !== 'undefined') {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
    }
};

export const setTokens = (accessToken: string, refreshToken: string) => {
    if (typeof window !== 'undefined') {
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("refresh_token", refreshToken);
    }
};

export const getAccessToken = () => {
    if (typeof window !== 'undefined') {
        return localStorage.getItem("access_token");
    }
    return null;
};

// Generic request handler
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = getAccessToken();

    const headers: any = {
        "Content-Type": "application/json",
        ...options.headers,
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const config: RequestInit = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        const data = await response.json();

        if (!response.ok) {
            // Handle 401 Unauthorized - could redirect to login or clear tokens
            if (response.status === 401) {
                clearTokens();
            }
            throw new Error(data.error || data.message || `API Error: ${response.status}`);
        }

        return data as T;
    } catch (error) {
        console.error(`API Request failed for ${endpoint}:`, error);
        throw error;
    }
}

export const api = {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: "GET" }),

    post: <T>(endpoint: string, body: any) =>
        request<T>(endpoint, {
            method: "POST",
            body: JSON.stringify(body)
        }),

    put: <T>(endpoint: string, body: any) =>
        request<T>(endpoint, {
            method: "PUT",
            body: JSON.stringify(body)
        }),

    delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),

    // Auth methods
    login: (email: string, password: string) =>
        request<any>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        }),

    signup: (email: string, name: string, password: string) =>
        request<any>("/auth/signup", {
            method: "POST",
            body: JSON.stringify({ email, name, password }),
        }),

    // User Playlist methods
    getUserPlaylists: (email: string) =>
        request<any>(`/user/${email}/playlists`),

    deleteUserPlaylist: (email: string, playlistId: string) =>
        request<any>(`/user/${email}/playlist/${playlistId}`, { method: "DELETE" }),

    saveUserPlaylist: (email: string, playlistId: string, playlistUrl: string, playlistTitle: string, totalVideos: number) =>
        request<any>(`/user/${email}/playlist`, {
            method: "POST",
            body: JSON.stringify({
                playlist_id: playlistId,
                playlist_url: playlistUrl,
                playlist_title: playlistTitle,
                total_videos: totalVideos
            }),
        }),

    // Video Learning methods
    getPlaylistVideos: (playlistUrl: string) =>
        request<any>("/playlist/videos", {
            method: "POST",
            body: JSON.stringify({ playlist_url: playlistUrl }),
        }),

    getVideoStatus: (videoId: string) =>
        request<any>(`/video/${videoId}/status`),

    processVideo: (youtubeUrl: string) =>
        request<any>("/video/process", {
            method: "POST",
            body: JSON.stringify({ youtube_url: youtubeUrl }),
        }),

    cancelVideoProcessing: (videoId: string) =>
        request<any>(`/video/${videoId}/cancel`, { method: "POST" }),

    getFrameAtTimestamp: (videoId: string, timestamp: number) =>
        request<any>(`/video/${videoId}/frame?timestamp=${timestamp}`),

    // Progress methods
    getPlaylistProgress: (email: string, playlistId: string) =>
        request<any>(`/user/${email}/playlist/${playlistId}/progress`),

    saveVideoProgress: (email: string, playlistId: string, videoId: string, watchedSeconds: number, videoDuration: number, completed: boolean) =>
        request<any>(`/user/${email}/playlist/${playlistId}/progress`, {
            method: "POST",
            body: JSON.stringify({
                video_id: videoId,
                watched_seconds: watchedSeconds,
                video_duration: videoDuration,
                completed: completed
            }),
        }),

    // Transcript search methods
    searchTranscript: (videoId: string, query: string, caseSensitive?: boolean) =>
        request<any>(`/video/${videoId}/transcript/search?query=${encodeURIComponent(query)}${caseSensitive ? '&case_sensitive=true' : ''}`),

    // Concept detection methods
    getDetectedConcepts: (videoId: string) =>
        request<any>(`/video/${videoId}/concepts`),

    detectConcepts: (videoId: string) =>
        request<any>(`/video/${videoId}/concepts/detect`, {
            method: "POST",
        }),
};
