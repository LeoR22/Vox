import React, { useState, useEffect, useCallback } from 'react';
import { Box, TextField, Button, Typography, IconButton, Paper } from '@mui/material';
import { PhotoCamera, Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';
import Post from './Post';

const Feed = ({ token, userId, userName }) => {
    const [posts, setPosts] = useState([]);
    const [newPost, setNewPost] = useState('');
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [message, setMessage] = useState('');
    const [searchQuery, setSearchQuery] = useState('');

    const API_URL = 'http://localhost:8000';

    const fetchPosts = useCallback(async () => {
        try {
            const response = await axios.get(`${API_URL}/posts`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            // Enriquecer posts con el nombre del usuario actual (simplificado)
            const enrichedPosts = response.data.map((post) => ({
                ...post,
                userName: post.user_id === userId ? userName : 'Desconocido', // Temporal hasta implementar GET /users
            }));
            setPosts(enrichedPosts);
            setMessage('');
        } catch (error) {
            setMessage('Error al obtener posts: ' + (error.response?.data?.detail || error.message));
        }
    }, [token, userId, userName]);

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            setImagePreview(URL.createObjectURL(file));
        }
    };

    const handleCreatePost = async () => {
        if (!newPost.trim() && !imageFile) {
            setMessage('El post no puede estar vacío');
            return;
        }
        try {
            const formData = new FormData();
            formData.append('content', newPost);
            formData.append('user_id', userId);
            if (imageFile) {
                formData.append('image', imageFile);
            }
            await axios.post(`${API_URL}/posts`, formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data',
                },
            });
            setNewPost('');
            setImageFile(null);
            setImagePreview(null);
            setMessage('Post publicado con éxito');
            fetchPosts();
        } catch (error) {
            console.error('Error al crear post:', error);
            setMessage('Error al crear post: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchPosts();
    }, [fetchPosts]);

    return (
        <Box sx={{ display: 'flex', gap: 3 }}>
            {/* Sección principal (publicaciones) */}
            <Box sx={{ flex: 2, maxWidth: '600px' }}>
                <Box sx={{ mb: 3 }}>
                    <TextField
                        placeholder="Buscar en Vox"
                        variant="outlined"
                        size="small"
                        sx={{
                            bgcolor: '#3a3b3c',
                            borderRadius: 5,
                            input: { color: '#fff' },
                            '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                            width: '100%',
                        }}
                        InputProps={{
                            startAdornment: <SearchIcon sx={{ color: '#fff', mr: 1 }} />,
                        }}
                    />
                </Box>
                <Paper sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
                    <TextField
                        fullWidth
                        placeholder="¿Qué está pasando?"
                        value={newPost}
                        onChange={(e) => setNewPost(e.target.value)}
                        multiline
                        rows={2}
                        variant="standard"
                        InputProps={{ disableUnderline: true, style: { color: '#fff' } }}
                    />
                    {imagePreview && (
                        <Box sx={{ mt: 1 }}>
                            <img
                                src={imagePreview}
                                alt="Vista previa"
                                style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '8px' }}
                            />
                        </Box>
                    )}
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <IconButton color="primary" component="label">
                            <PhotoCamera sx={{ color: '#fff' }} />
                            <input type="file" accept="image/*" hidden onChange={handleImageChange} />
                        </IconButton>
                        <Button
                            variant="contained"
                            sx={{
                                background: 'linear-gradient(90deg, #F87224, #D9332E)',
                                color: '#fff',
                                borderRadius: 20,
                                ml: 1,
                                '&:hover': {
                                    background: 'linear-gradient(90deg, #E69520, #C9302C)',
                                },
                            }}
                            onClick={handleCreatePost}
                        >
                            Publicar
                        </Button>
                    </Box>
                </Paper>
                {message && (
                    <Typography color={message.includes('éxito') ? '#f5a623' : 'error'} sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                )}
                {posts.length === 0 && !message ? (
                    <Typography sx={{ color: '#fff' }}>No hay posts para mostrar</Typography>
                ) : (
                    posts.map((post) => (
                        <Post
                            key={post._id}
                            post={post}
                            token={token}
                            userId={userId}
                            userName={userName}
                            fetchPosts={fetchPosts}
                        />
                    ))
                )}
            </Box>

            {/* Sección de tendencias */}
            <Box sx={{ flex: 1, maxWidth: '350px' }}>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                    Qué está sucediendo
                </Typography>
                <Paper sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
                    <Typography>[Placeholder para tendencias]</Typography>
                </Paper>
            </Box>
        </Box>
    );
};

export default Feed;