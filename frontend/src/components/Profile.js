import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, IconButton, Paper, Avatar, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { PhotoCamera, Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';
import Post from './Post';

const Profile = ({ token, userId, userName }) => {
    const [profile, setProfile] = useState(null);
    const [posts, setPosts] = useState([]);
    const [message, setMessage] = useState('');
    const [profileImageFile, setProfileImageFile] = useState(null);
    const [coverImageFile, setCoverImageFile] = useState(null);
    const [profileImagePreview, setProfileImagePreview] = useState(null);
    const [coverImagePreview, setCoverImagePreview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [openEditDialog, setOpenEditDialog] = useState(false);
    const [editBio, setEditBio] = useState('');
    const [editName, setEditName] = useState('');

    const API_URL = 'http://localhost:8000';

    const fetchProfile = async () => {
        try {
            console.log('Fetching profile for userId:', userId);
            const response = await axios.get(`${API_URL}/users/${userId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            console.log('Profile data:', response.data);
            setProfile(response.data);
            setEditBio(response.data.bio || '');
            setEditName(response.data.name || userName);
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setError(`Error al obtener perfil: ${errorMessage}`);
            console.error('Error en fetchProfile:', error);
        }
    };

    const fetchPosts = async () => {
        try {
            console.log('Fetching posts');
            const response = await axios.get(`${API_URL}/posts`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            console.log('Posts data:', response.data);
            const enrichedPosts = response.data
                .filter((post) => post.user_id === userId)
                .map((post) => ({
                    ...post,
                    userName,
                }));
            setPosts(enrichedPosts);
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setError(`Error al obtener posts: ${errorMessage}`);
            console.error('Error en fetchPosts:', error);
        }
    };

    const handleProfileImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setProfileImageFile(file);
            setProfileImagePreview(URL.createObjectURL(file));
        }
    };

    const handleCoverImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setCoverImageFile(file);
            setCoverImagePreview(URL.createObjectURL(file));
        }
    };

    const handleUpdateProfile = async () => {
        try {
            const formData = new FormData();
            if (profileImageFile) {
                formData.append('profile_image', profileImageFile);
            }
            if (coverImageFile) {
                formData.append('cover_image', coverImageFile);
            }
            console.log('Sending update request with profileImageFile:', profileImageFile, 'coverImageFile:', coverImageFile);
            const response = await axios.put(`${API_URL}/users/${userId}`, formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            console.log('Update response:', response.data);
            setMessage('Perfil actualizado con éxito');
            setProfileImageFile(null);
            setCoverImageFile(null);
            setProfileImagePreview(null);
            setCoverImagePreview(null);
            await fetchProfile();
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Error al actualizar perfil: ${errorMessage}`);
            console.error('Error en handleUpdateProfile:', error);
        }
    };

    const handleEditProfile = () => {
        setOpenEditDialog(true);
    };

    const handleCloseEditDialog = () => {
        setOpenEditDialog(false);
        setEditBio(profile?.bio || '');
        setEditName(profile?.name || userName);
    };

    const handleSaveEditProfile = async () => {
        try {
            const formData = new FormData();
            formData.append('bio', editBio);
            formData.append('name', editName);
            console.log('Sending edit profile request with bio:', editBio, 'name:', editName);
            const response = await axios.put(`${API_URL}/users/${userId}`, formData, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            console.log('Edit profile response:', response.data);
            setMessage('Perfil actualizado con éxito');
            setOpenEditDialog(false);
            await fetchProfile();
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Error al actualizar perfil: ${errorMessage}`);
            console.error('Error en handleSaveEditProfile:', error);
        }
    };

    useEffect(() => {
        if (!token || !userId || !userName) {
            setError('Faltan datos de autenticación');
            setLoading(false);
            return;
        }
        const loadData = async () => {
            setLoading(true);
            await Promise.all([fetchProfile(), fetchPosts()]);
            setLoading(false);
        };
        loadData();
    }, [userId, token, userName]);

    if (loading) {
        return <Typography sx={{ color: '#fff' }}>Cargando perfil...</Typography>;
    }

    return (
        <Box sx={{ display: 'flex', gap: 3 }}>
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
                    <Box sx={{ position: 'relative', height: 150, bgcolor: '#1a1a1a', mb: 4 }}>
                        {profile?.cover_image_url || coverImagePreview ? (
                            <img
                                src={coverImagePreview || `${API_URL}${profile.cover_image_url}`}
                                alt="Portada"
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                onError={() => console.error('Error loading cover image:', profile.cover_image_url)}
                            />
                        ) : (
                            <Box sx={{ width: '100%', height: '100%', bgcolor: '#1a1a1a' }} />
                        )}
                        <IconButton component="label" sx={{ position: 'absolute', top: 8, right: 8, color: '#fff' }}>
                            <PhotoCamera />
                            <input type="file" accept="image/*" hidden onChange={handleCoverImageChange} />
                        </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, mt: -8 }}>
                        <Avatar
                            src={profile?.profile_image_url ? `${API_URL}${profile.profile_image_url}` : profileImagePreview}
                            sx={{ width: 80, height: 80, border: '2px solid #292A2C', bgcolor: '#3a3b3c' }}
                            onError={() => console.error('Error loading profile image:', profile.profile_image_url)}
                        />
                        <IconButton component="label" sx={{ ml: -2, mt: 4, color: '#fff' }}>
                            <PhotoCamera />
                            <input type="file" accept="image/*" hidden onChange={handleProfileImageChange} />
                        </IconButton>
                    </Box>
                    <Typography variant="h6">{userName}</Typography>
                    <Typography variant="body2" sx={{ color: '#aaa' }}>
                        @{userName.toLowerCase().replace(/\s+/g, '')}
                    </Typography>
                    <Typography sx={{ my: 1 }}>{profile?.bio || 'Sin biografía'}</Typography>
                    <Typography sx={{ color: '#aaa' }}>
                        Se unió en {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }) : '-'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, my: 1 }}>
                        <Typography>
                            <strong>{profile?.following_count || 0}</strong> Siguiendo
                        </Typography>
                        <Typography>
                            <strong>{profile?.followers_count || 0}</strong> Seguidores
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                            variant="contained"
                            sx={{
                                background: 'linear-gradient(90deg, #F87224, #D9332E)',
                                color: '#fff',
                                borderRadius: 20,
                                mt: 2,
                                '&:hover': {
                                    background: 'linear-gradient(90deg, #E69520, #C9302C)',
                                },
                            }}
                            onClick={handleUpdateProfile}
                        >
                            Guardar cambios
                        </Button>
                        <Button
                            variant="outlined"
                            sx={{
                                color: '#fff',
                                borderColor: '#fff',
                                borderRadius: 20,
                                mt: 2,
                                '&:hover': {
                                    borderColor: '#f5a623',
                                    color: '#f5a623',
                                },
                            }}
                            onClick={handleEditProfile}
                        >
                            Editar perfil
                        </Button>
                    </Box>
                </Paper>
                {error && (
                    <Typography sx={{ color: '#ff4d4f', mb: 2, bgcolor: '#3a3b3c', p: 1, borderRadius: 1 }}>
                        {error}
                    </Typography>
                )}
                <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                    Publicaciones
                </Typography>
                {posts.length === 0 ? (
                    <Typography sx={{ color: '#fff' }}>No hay publicaciones</Typography>
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
                {message && (
                    <Typography sx={{ mt: 2, color: message.includes('éxito') ? '#f5a623' : '#ff4d4f' }}>
                        {message}
                    </Typography>
                )}
                <Dialog open={openEditDialog} onClose={handleCloseEditDialog}>
                    <DialogTitle>Editar perfil</DialogTitle>
                    <DialogContent>
                        <TextField
                            label="Nombre"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            fullWidth
                            margin="normal"
                            inputProps={{ maxLength: 50 }}
                            sx={{ bgcolor: '#3a3b3c', color: '#fff', input: { color: '#fff' } }}
                        />
                        <TextField
                            label="Biografía"
                            value={editBio}
                            onChange={(e) => setEditBio(e.target.value)}
                            fullWidth
                            multiline
                            rows={4}
                            margin="normal"
                            inputProps={{ maxLength: 160 }}
                            sx={{ bgcolor: '#3a3b3c', color: '#fff', input: { color: '#fff' }, textarea: { color: '#fff' } }}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={handleCloseEditDialog} sx={{ color: '#fff' }}>
                            Cancelar
                        </Button>
                        <Button onClick={handleSaveEditProfile} sx={{ color: '#f5a623' }}>
                            Guardar
                        </Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </Box>
    );
};

export default Profile;