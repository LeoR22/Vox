import React, { useState, useEffect, useCallback } from 'react';
import { Box, TextField, Button, Typography } from '@mui/material';
import axios from 'axios';
import Post from './Post';

const Feed = ({ token, userId }) => {
    const [posts, setPosts] = useState([]);
    const [newPost, setNewPost] = useState('');
    const [message, setMessage] = useState('');

    const API_URL = 'http://localhost:8000';

    const fetchPosts = useCallback(async () => {
        try {
            const response = await axios.get(`${API_URL}/posts`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            // Obtener información de los usuarios para mostrar sus nombres
            const userResponse = await axios.get(`${API_URL}/users`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const users = userResponse.data;
            const enrichedPosts = response.data.map((post) => {
                const user = users.find((u) => u._id === post.user_id);
                return { ...post, userName: user ? user.name : 'Desconocido' };
            });
            setPosts(enrichedPosts);
        } catch (error) {
            setMessage('Error al obtener posts: ' + (error.response?.data?.detail || error.message));
        }
    }, [token]);

    const handleCreatePost = async () => {
        if (!newPost.trim()) {
            setMessage('El post no puede estar vacío');
            return;
        }
        try {
            await axios.post(
                `${API_URL}/posts`,
                { content: newPost, user_id: userId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewPost('');
            setMessage('Post publicado con éxito');
            fetchPosts();
        } catch (error) {
            setMessage('Error al crear post: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchPosts();
    }, [fetchPosts]);

    return (
        <Box sx={{ flex: 1, p: 2 }}>
            <Box sx={{ mb: 2 }}>
                <TextField
                    fullWidth
                    placeholder="¿Qué está pasando?"
                    value={newPost}
                    onChange={(e) => setNewPost(e.target.value)}
                    multiline
                    rows={2}
                    variant="outlined"
                />
                <Button
                    variant="contained"
                    color="primary"
                    sx={{ mt: 1, borderRadius: 20 }}
                    onClick={handleCreatePost}
                >
                    Publicar
                </Button>
            </Box>
            {message && (
                <Typography color={message.includes('éxito') ? 'primary' : 'error'} sx={{ mb: 2 }}>
                    {message}
                </Typography>
            )}
            {posts.length === 0 ? (
                <Typography>No hay posts para mostrar</Typography>
            ) : (
                posts.map((post) => (
                    <Post
                        key={post._id}
                        post={post}
                        token={token}
                        userId={userId}
                        fetchPosts={fetchPosts}
                        userName={post.userName}
                    />
                ))
            )}
        </Box>
    );
};

export default Feed;