import React, { useState } from 'react';
import { Box, Typography, IconButton, TextField, Button } from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import FavoriteIcon from '@mui/icons-material/Favorite';
import CommentIcon from '@mui/icons-material/Comment';
import axios from 'axios';

const Post = ({ post, token, userId, fetchPosts, userName }) => {
    const [showComments, setShowComments] = useState(false);
    const [newComment, setNewComment] = useState('');
    const [comments, setComments] = useState([]);
    const [liked, setLiked] = useState(false);

    const API_URL = 'http://localhost:8000';

    const fetchComments = async () => {
        try {
            const response = await axios.get(`${API_URL}/comments/post/${post._id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setComments(response.data);
        } catch (error) {
            console.error('Error al obtener comentarios:', error);
        }
    };

    const handleLike = async () => {
        try {
            await axios.post(
                `${API_URL}/likes/post/${post._id}`,
                { user_id: userId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setLiked(true);
            fetchPosts();
        } catch (error) {
            console.error('Error al dar like:', error);
        }
    };

    const handleComment = async () => {
        try {
            await axios.post(
                `${API_URL}/comments`,
                { post_id: post._id, user_id: userId, content: newComment },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewComment('');
            fetchComments();
        } catch (error) {
            console.error('Error al comentar:', error);
        }
    };

    return (
        <Box sx={{ borderBottom: '1px solid #e0e0e0', p: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold">
                {userName}
            </Typography>
            <Typography variant="body1">{post.content}</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <IconButton onClick={handleLike}>
                    {liked ? <FavoriteIcon color="error" /> : <FavoriteBorderIcon />}
                </IconButton>
                <IconButton onClick={() => { setShowComments(!showComments); fetchComments(); }}>
                    <CommentIcon />
                </IconButton>
            </Box>
            {showComments && (
                <Box sx={{ mt: 2 }}>
                    <TextField
                        fullWidth
                        placeholder="Añade un comentario..."
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        variant="outlined"
                        size="small"
                    />
                    <Button
                        variant="contained"
                        color="primary"
                        sx={{ mt: 1, borderRadius: 20 }}
                        onClick={handleComment}
                    >
                        Comentar
                    </Button>
                    {comments.map((comment) => (
                        <Box key={comment._id} sx={{ mt: 1 }}>
                            <Typography variant="body2">{comment.content}</Typography>
                            <Typography variant="caption" color="textSecondary">
                                Por: {comment.user_id}
                            </Typography>
                        </Box>
                    ))}
                </Box>
            )}
        </Box>
    );
};

export default Post;