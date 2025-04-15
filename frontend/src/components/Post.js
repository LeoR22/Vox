import React, { useState, useEffect } from 'react';
import { Box, Typography, TextField, Button, IconButton, Paper } from '@mui/material';
import { Favorite, FavoriteBorder, Comment } from '@mui/icons-material';
import axios from 'axios';

const Post = ({ post, token, userId, userName, fetchPosts }) => {
    const [newComment, setNewComment] = useState('');
    const [comments, setComments] = useState(post.comments || []);
    const [likes, setLikes] = useState(post.likes || []);
    const [message, setMessage] = useState('');

    const API_URL = 'http://localhost:8000';

    const handleLike = async () => {
        try {
            console.log('Enviando like:', { user_id: userId });
            await axios.post(
                `${API_URL}/posts/${post._id}/likes`,
                { user_id: userId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setLikes((prev) => (prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]));
            fetchPosts();
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Error al dar Me gusta: ${errorMessage}`);
            console.error('Error en handleLike:', error.response?.data || error);
        }
    };

    const handleAddComment = async () => {
        if (!newComment.trim()) {
            setMessage('El comentario no puede estar vacío');
            return;
        }
        try {
            const response = await axios.post(
                `${API_URL}/posts/${post._id}/comments`,
                { content: newComment, user_id: userId, user_name: userName },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setComments((prev) => [...prev, response.data]);
            setNewComment('');
            setMessage('Comentario añadido con éxito');
            fetchPosts();
        } catch (error) {
            setMessage('Error al añadir comentario: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        setComments(post.comments || []);
        setLikes(post.likes || []);
    }, [post]);

    return (
        <Paper sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
            <Typography variant="subtitle1">{post.userName}</Typography>
            <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                @{post.userName.toLowerCase().replace(/\s+/g, '')}
            </Typography>
            <Typography>{post.content}</Typography>
            {post.image_url ? (
                <Box sx={{ mt: 1 }}>
                    {console.log('Image URL:', `${API_URL}${post.image_url}`)}
                    <img
                        src={`${API_URL}${post.image_url}`}
                        alt="Post"
                        style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }}
                        onError={(e) => console.error('Error cargando imagen:', e)}
                    />
                </Box>
            ) : (
                console.log('No image_url en post:', post)
            )}
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <IconButton onClick={handleLike}>
                    {likes.includes(userId) ? (
                        <Favorite sx={{ color: '#f5a623' }} />
                    ) : (
                        <FavoriteBorder sx={{ color: '#fff' }} />
                    )}
                </IconButton>
                <Typography sx={{ mr: 2 }}>{likes.length}</Typography>
                <IconButton>
                    <Comment sx={{ color: '#fff' }} />
                </IconButton>
                <Typography>{comments.length}</Typography>
            </Box>
            <Box sx={{ mt: 2 }}>
                {comments.map((comment, index) => (
                    <Box key={index} sx={{ ml: 2, mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ color: '#fff' }}>
                            {comment.user_name}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#aaa' }}>
                            {comment.content}
                        </Typography>
                    </Box>
                ))}
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <TextField
                        placeholder="Añadir un comentario"
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        variant="outlined"
                        size="small"
                        sx={{
                            bgcolor: '#2a2b2c',
                            borderRadius: 2,
                            input: { color: '#fff' },
                            '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                            flex: 1,
                            mr: 1,
                        }}
                    />
                    <Button
                        variant="contained"
                        sx={{
                            background: 'linear-gradient(90deg, #F87224, #D9332E)',
                            color: '#fff',
                            borderRadius: 20,
                            '&:hover': {
                                background: 'linear-gradient(90deg, #E69520, #C9302C)',
                            },
                        }}
                        onClick={handleAddComment}
                    >
                        Comentar
                    </Button>
                </Box>
            </Box>
            {message && (
                <Typography
                    sx={{ mt: 1, color: message.includes('éxito') ? '#f5a623' : 'error.main' }}
                >
                    {message}
                </Typography>
            )}
        </Paper>
    );
};

export default Post;