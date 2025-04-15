import React, { useState, useEffect } from 'react';
import { Box, Typography, TextField, List, ListItem, ListItemAvatar, ListItemText, Avatar, Button, CircularProgress } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';

const Explore = ({ token, userId }) => {
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [message, setMessage] = useState('');
    const [followingStatus, setFollowingStatus] = useState({});

    const API_URL = 'http://localhost:8000';

    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('Token enviado en fetchUsers:', token);

            // Obtener la lista de usuarios
            try {
                const usersResponse = await axios.get(`${API_URL}/users`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                console.log('Users data:', usersResponse.data);
                setUsers(usersResponse.data);
                setFilteredUsers(usersResponse.data);
            } catch (error) {
                const errorMessage = error.response?.data?.detail || error.message;
                setError(`Error al obtener usuarios: ${errorMessage}`);
                console.error('Error en fetchUsers (users):', error);
                return; // Salir si falla la carga de usuarios
            }

            // Obtener la lista de usuarios que el usuario actual sigue
            try {
                const followingResponse = await axios.get(`${API_URL}/friends/following/${userId}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                console.log('Following data:', followingResponse.data);
                const followingMap = {};
                followingResponse.data.forEach((followedUser) => {
                    followingMap[followedUser.followed_id] = true;
                });
                setFollowingStatus(followingMap);
            } catch (error) {
                const errorMessage = error.response?.data?.detail || error.message;
                console.error('Error en fetchUsers (following):', errorMessage);
                // No seteamos error aquí para no afectar la lista de usuarios
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        const query = e.target.value.toLowerCase();
        setSearchQuery(query);
        const filtered = users.filter(
            (user) =>
                user.name.toLowerCase().includes(query) ||
                user.user_id.toLowerCase().includes(query)
        );
        setFilteredUsers(filtered);
    };

    const handleFollow = async (followId) => {
        try {
            console.log('Token enviado en handleFollow:', token);
            const response = await axios.post(
                `${API_URL}/friends/follow/${followId}`,
                { user_id: userId },
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            setMessage(`Ahora sigues a ${followId}`);
            console.log('Follow response:', response.data);
            setFollowingStatus((prev) => ({
                ...prev,
                [followId]: true,
            }));
            fetchUsers();
        } catch (error) {
            const errorMessage = error.response?.data?.detail || error.message;
            setMessage(`Error al seguir a ${followId}: ${errorMessage}`);
            console.error('Error en handleFollow:', error);
        }
    };

    useEffect(() => {
        if (!token || !userId) {
            setError('Faltan datos de autenticación');
            setLoading(false);
            return;
        }
        fetchUsers();
    }, [token, userId]);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                <CircularProgress sx={{ color: '#fff' }} />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3, maxWidth: '600px', mx: 'auto' }}>
            <Typography variant="h5" sx={{ color: '#fff', mb: 2 }}>
                Explorar
            </Typography>
            {error && (
                <Typography sx={{ color: '#ff4d4f', mb: 2, bgcolor: '#3a3b3c', p: 1, borderRadius: 1 }}>
                    {error}
                </Typography>
            )}
            <Box sx={{ mb: 3 }}>
                <TextField
                    placeholder="Buscar usuarios"
                    variant="outlined"
                    size="small"
                    value={searchQuery}
                    onChange={handleSearch}
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
            {message && (
                <Typography sx={{ mt: 2, color: message.includes('sigues') ? '#f5a623' : '#ff4d4f' }}>
                    {message}
                </Typography>
            )}
            <List sx={{ bgcolor: '#3a3b3c', borderRadius: 2 }}>
                {filteredUsers.length === 0 ? (
                    <Typography sx={{ color: '#fff', p: 2 }}>
                        No se encontraron usuarios
                    </Typography>
                ) : (
                    filteredUsers.map((user) => (
                        <ListItem
                            key={user.user_id}
                            sx={{
                                borderBottom: '1px solid #4a4b4c',
                                '&:last-child': { borderBottom: 'none' },
                            }}
                        >
                            <ListItemAvatar>
                                <Avatar
                                    src={user.profile_image_url ? `${API_URL}${user.profile_image_url}` : undefined}
                                    sx={{ bgcolor: '#3a3b3c' }}
                                />
                            </ListItemAvatar>
                            <ListItemText
                                primary={<Typography sx={{ color: '#fff' }}>{user.name}</Typography>}
                                secondary={
                                    <Typography sx={{ color: '#aaa' }}>
                                        @{user.user_id.toLowerCase().replace(/\s+/g, '')}
                                    </Typography>
                                }
                            />
                            {user.user_id !== userId && (
                                <Button
                                    variant="contained"
                                    sx={{
                                        background: followingStatus[user.user_id]
                                            ? '#4a4b4c'
                                            : 'linear-gradient(90deg, #F87224, #D9332E)',
                                        color: '#fff',
                                        borderRadius: 20,
                                        '&:hover': {
                                            background: followingStatus[user.user_id]
                                                ? '#5a5b5c'
                                                : 'linear-gradient(90deg, #E69520, #C9302C)',
                                        },
                                    }}
                                    onClick={() => handleFollow(user.user_id)}
                                >
                                    {followingStatus[user.user_id] ? 'Siguiendo' : 'Seguir'}
                                </Button>
                            )}
                        </ListItem>
                    ))
                )}
            </List>
        </Box>
    );
};

export default Explore;