import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';
import Post from './Post';

const Bookmarks = ({ token, userId, userName }) => {
    const [bookmarks, setBookmarks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const API_URL = 'http://localhost:8000';

    const fetchBookmarks = async () => {
        try {
            setLoading(true);
            // Fetch bookmark entries
            const bookmarkResponse = await axios.get(`${API_URL}/bookmarks/user/${userId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const bookmarkPostIds = bookmarkResponse.data.map((bookmark) => bookmark.post_id);

            // Fetch post details for each bookmarked post
            const postPromises = bookmarkPostIds.map((postId) =>
                axios.get(`${API_URL}/posts/${postId}`, {
                    headers: { Authorization: `Bearer ${token}` },
                })
            );
            const postResponses = await Promise.all(postPromises);
            const enrichedPosts = postResponses.map((response) => ({
                ...response.data,
                userName: response.data.user_id === userId ? userName : 'Desconocido',
            }));

            setBookmarks(enrichedPosts);
            setError('');
        } catch (error) {
            setError('Error al obtener bookmarks: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBookmarks();
    }, [token, userId]);

    return (
        <Box sx={{ p: 3, maxWidth: '600px', mx: 'auto' }}>
            <Typography variant="h5" sx={{ color: '#fff', mb: 2 }}>
                Guardados
            </Typography>
            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                    <CircularProgress sx={{ color: '#fff' }} />
                </Box>
            ) : error ? (
                <Typography sx={{ color: '#ff4d4f', mb: 2 }}>{error}</Typography>
            ) : bookmarks.length === 0 ? (
                <Typography sx={{ color: '#fff' }}>No tienes posts guardados</Typography>
            ) : (
                bookmarks.map((post) => (
                    <Post
                        key={post._id}
                        post={post}
                        token={token}
                        userId={userId}
                        userName={userName}
                        fetchPosts={fetchBookmarks}
                    />
                ))
            )}
        </Box>
    );
};

export default Bookmarks;