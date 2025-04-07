import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, Button, TextField, List, ListItem, ListItemText, ListItemIcon, Avatar, IconButton } from '@mui/material'; // Eliminamos Divider
import { Link } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import ExploreIcon from '@mui/icons-material/Explore';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MessageIcon from '@mui/icons-material/Message';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ListIcon from '@mui/icons-material/List';
import PersonIcon from '@mui/icons-material/Person';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import axios from 'axios';

const Sidebar = ({ token, userId, userName, onLogout }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [users, setUsers] = useState([]);
    const [following, setFollowing] = useState([]);
    const [message, setMessage] = useState('');

    const API_URL = 'http://localhost:8000';

    const searchUsers = async () => {
        try {
            const response = await axios.get(`${API_URL}/users`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const filteredUsers = response.data.filter(
                (user) =>
                    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    user.name.toLowerCase().includes(searchQuery.toLowerCase())
            );
            setUsers(filteredUsers);
        } catch (error) {
            setMessage('Error al buscar usuarios: ' + (error.response?.data?.detail || error.message));
        }
    };

    const fetchFollowing = useCallback(async () => {
        try {
            const response = await axios.get(`${API_URL}/friends/following/${userId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setFollowing(response.data);
        } catch (error) {
            setMessage('Error al obtener seguidos: ' + (error.response?.data?.detail || error.message));
        }
    }, [token, userId]);

    const handleFollow = async (followId) => {
        try {
            await axios.post(
                `${API_URL}/friends/follow/${followId}`,
                { follower_id: userId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setMessage('Usuario seguido con éxito');
            fetchFollowing();
        } catch (error) {
            setMessage('Error al seguir: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchFollowing();
    }, [fetchFollowing]);

    // Aseguramos que userName tenga un valor por defecto
    const displayName = userName || 'Usuario';
    const displayHandle = userName ? `@${userName.toLowerCase()}` : '@usuario';

    return (
        <Box sx={{ width: 250, p: 2, bgcolor: '#000', color: '#fff', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            {/* Opciones de Navegación */}
            <List>
                <ListItem button component={Link} to="/home">
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <HomeIcon />
                    </ListItemIcon>
                    <ListItemText primary="Home" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <ExploreIcon />
                    </ListItemIcon>
                    <ListItemText primary="Explorar" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <NotificationsIcon />
                    </ListItemIcon>
                    <ListItemText primary="Notificaciones" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <MessageIcon />
                    </ListItemIcon>
                    <ListItemText primary="Mensajes" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <BookmarkIcon />
                    </ListItemIcon>
                    <ListItemText primary="Guardados" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <ListIcon />
                    </ListItemIcon>
                    <ListItemText primary="Listas" />
                </ListItem>
                <ListItem button>
                    <ListItemIcon sx={{ color: '#fff' }}>
                        <PersonIcon />
                    </ListItemIcon>
                    <ListItemText primary="Perfil" />
                </ListItem>
            </List>

            {/* Botón Publicar */}
            <Button
                variant="contained"
                color="primary"
                startIcon={<AddCircleIcon />}
                sx={{ mt: 2, borderRadius: 20, bgcolor: '#ff6200', '&:hover': { bgcolor: '#e55a00' } }}
            >
                Publicar
            </Button>

            {/* Buscar Usuarios */}
            <Box sx={{ mt: 4 }}>
                <Typography variant="h6">Buscar Usuarios</Typography>
                <TextField
                    fullWidth
                    placeholder="Buscar por email o nombre"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    variant="outlined"
                    size="small"
                    sx={{ mt: 1, bgcolor: '#fff' }}
                />
                <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    sx={{ mt: 1, borderRadius: 20 }}
                    onClick={searchUsers}
                >
                    Buscar
                </Button>
                {users.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                        <Typography variant="h6">Resultados</Typography>
                        <List>
                            {users.map((user) => (
                                <ListItem key={user._id} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <ListItemText primary={user.name} secondary={user.email} />
                                    <Button
                                        variant="outlined"
                                        color="primary"
                                        size="small"
                                        onClick={() => handleFollow(user._id)}
                                        disabled={following.some((f) => f.following_id === user._id)}
                                    >
                                        {following.some((f) => f.following_id === user._id) ? 'Siguiendo' : 'Seguir'}
                                    </Button>
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}
                <Typography variant="h6" sx={{ mt: 2 }}>
                    Siguiendo
                </Typography>
                <List>
                    {following.map((user) => (
                        <ListItem key={user._id}>
                            <ListItemText primary={user.following_id} />
                        </ListItem>
                    ))}
                </List>
                {message && (
                    <Typography color="error" sx={{ mt: 2 }}>
                        {message}
                    </Typography>
                )}
            </Box>

            {/* Perfil y Cerrar Sesión */}
            <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: '#ff6200' }}>{displayName[0]}</Avatar>
                    <Box sx={{ ml: 2 }}>
                        <Typography variant="body1">{displayName}</Typography>
                        <Typography variant="caption" color="gray">
                            {displayHandle}
                        </Typography>
                    </Box>
                </Box>
                <IconButton onClick={onLogout} sx={{ color: '#fff' }}>
                    <LogoutIcon />
                </IconButton>
            </Box>
        </Box>
    );
};

export default Sidebar;