import React, { useState, useEffect } from 'react';
import { Box, Typography, TextField, Button, IconButton, Paper } from '@mui/material';
import { Favorite, FavoriteBorder, Comment, Bookmark, BookmarkBorder } from '@mui/icons-material';
import axios from 'axios';

const Post = ({ post, token, userId, userName, fetchPosts }) => {
    const [newComment, setNewComment] = useState('');
    const [comments, setComments] = useState(post.comments || []);
    const [likes, setLikes] = useState(post.likes || []);
    const [isBookmarked, setIsBookmarked] = useState(false);
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const API_URL = 'http://localhost:8000';

    // Check if post is bookmarked on mount
    useEffect(() => {
        const checkBookmark = async () => {
            try {
                const response = await axios.get(`${API_URL}/bookmarks/check`, {
                    params: { user_id: userId, post_id: post._id },
                    headers: { Authorization: `Bearer ${token}` },
                });
                setIsBookmarked(response.data.is_bookmarked);
            } catch (err) {
                console.error('Error checking bookmark:', err);
            }
        };
        checkBookmark();
    }, [post._id, userId, token]);

    // Handle post like toggle
    const handleLike = async () => {
        setLoading(true);
        setMessage('');

        try {
            const response = await axios.post(
                `${API_URL}/posts/${post._id}/likes`,
                `user_id=${userId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                }
            );
            if (response.data.action === 'added') {
                setLikes([...likes, userId]);
            } else {
                setLikes(likes.filter((id) => id !== userId));
            }
            fetchPosts();
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Error al dar Me gusta: ${errorMessage}`);
            console.error('Error en handleLike:', error.response?.data || error);
        } finally {
            setLoading(false);
        }
    };

    // Handle comment submission
    const handleAddComment = async () => {
        if (!newComment.trim()) {
            setMessage('El comentario no puede estar vacío');
            return;
        }
        setLoading(true);
        setMessage('');

        try {
            const response = await axios.post(
                `${API_URL}/posts/${post._id}/comments`,
                {
                    user_id: userId,
                    user_name: userName,
                    content: newComment,
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );
            setComments([...comments, response.data]);
            setNewComment('');
            setMessage('Comentario añadido con éxito');
            fetchPosts();
        } catch (error) {
            setMessage('Error al añadir comentario: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    // Handle comment like toggle
    const handleCommentLike = async (commentIndex) => {
        setLoading(true);
        setMessage('');

        try {
            const response = await axios.post(
                `${API_URL}/posts/${post._id}/comments/${commentIndex}/likes`,
                `user_id=${userId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                }
            );
            const updatedComments = [...comments];
            const commentLikes = updatedComments[commentIndex].likes || [];
            if (response.data.action === 'added') {
                updatedComments[commentIndex].likes = [...commentLikes, userId];
            } else {
                updatedComments[commentIndex].likes = commentLikes.filter((id) => id !== userId);
            }
            setComments(updatedComments);
            fetchPosts();
        } catch (error) {
            setMessage('Error al dar Me gusta al comentario: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    // Handle bookmark toggle
    const handleBookmark = async () => {
        setLoading(true);
        setMessage('');

        try {
            const response = await axios.post(
                `${API_URL}/bookmarks`,
                {
                    user_id: userId,
                    post_id: post._id,
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                }
            );
            setIsBookmarked(response.data.action === 'added');
            setMessage(response.data.action === 'added' ? 'Post guardado' : 'Post eliminado de guardados');
            fetchPosts();
        } catch (error) {
            setMessage('Error al gestionar bookmark: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <Paper sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
            <Typography variant="subtitle1">{post.user_id}</Typography>
            <Typography variant="body2" sx={{ color: '#aaa', mb: 1 }}>
                @{post.user_id.toLowerCase().replace(/\s+/g, '')}
            </Typography>
            <Typography>{post.content}</Typography>
            {post.image_url && (
                <Box sx={{ mt: 1 }}>
                    <img
                        src={`${API_URL}${post.image_url}`}
                        alt="Post"
                        style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px' }}
                        onError={(e) => console.error('Error cargando imagen:', e)}
                    />
                </Box>
            )}
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <IconButton onClick={handleLike} disabled={loading}>
                    {likes.includes(userId) ? (
                        <Favorite sx={{ color: '#f5a623' }} />
                    ) : (
                        <FavoriteBorder sx={{ color: '#fff' }} />
                    )}
                </IconButton>
                <Typography sx={{ mr: 2 }}>{likes.length}</Typography>
                <IconButton disabled>
                    <Comment sx={{ color: '#fff' }} />
                </IconButton>
                <Typography sx={{ mr: 2 }}>{comments.length}</Typography>
                <IconButton onClick={handleBookmark} disabled={loading}>
                    {isBookmarked ? (
                        <Bookmark sx={{ color: '#f5a623' }} />
                    ) : (
                        <BookmarkBorder sx={{ color: '#fff' }} />
                    )}
                </IconButton>
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
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                            <IconButton
                                onClick={() => handleCommentLike(index)}
                                disabled={loading}
                                size="small"
                            >
                                {comment.likes?.includes(userId) ? (
                                    <Favorite sx={{ color: '#f5a623', fontSize: 16 }} />
                                ) : (
                                    <FavoriteBorder sx={{ color: '#fff', fontSize: 16 }} />
                                )}
                            </IconButton>
                            <Typography variant="caption" sx={{ color: '#fff' }}>
                                {comment.likes?.length || 0}
                            </Typography>
                        </Box>
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
                        disabled={loading}
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
                        disabled={loading || !newComment.trim()}
                    >
                        Comentar
                    </Button>
                </Box>
            </Box>
            {message && (
                <Typography
                    sx={{ mt: 1, color: message.includes('éxito') || message.includes('guardado') ? '#f5a623' : 'error.main' }}
                >
                    {message}
                </Typography>
            )}
        </Paper>
    );
};

export default Post;