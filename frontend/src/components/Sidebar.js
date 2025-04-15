import React from 'react';
import { Box, List, ListItem, ListItemIcon, ListItemText, Button, Typography, IconButton } from '@mui/material';
import { Home, Explore, Notifications, Message, Bookmark, ListAlt, Person, MoreHoriz, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const Sidebar = ({ handleLogout, userName, userId }) => {
    const navigate = useNavigate();

    // Usamos "/profile/" para coincidir con la ruta definida en App.js
    const profilePath = `/profile/${userName}`;

    const menuItems = [
        { text: 'Home', icon: <Home />, path: '/home' },
        { text: 'Explorar', icon: <Explore />, path: '/explore' },
        { text: 'Notificaciones', icon: <Notifications />, path: '/notifications' },
        { text: 'Mensajes', icon: <Message />, path: '/messages' },
        { text: 'Guardados', icon: <Bookmark />, path: '/bookmarks' },
        { text: 'Listas', icon: <ListAlt />, path: '/lists' },
        { text: 'Perfil', icon: <Person />, path: profilePath },
        { text: 'Más', icon: <MoreHoriz />, path: '/more' },
    ];

    const handleNavigation = (path) => {
        console.log('Navigating to:', path);
        navigate(path);
    };

    return (
        <Box
            sx={{
                width: { xs: '100%', md: 275 },
                maxWidth: 275,
                bgcolor: '#292A2C',
                p: 2,
                borderRight: { md: '1px solid #3a3b3c' },
                position: { md: 'fixed' },
                height: { md: '100vh' },
                top: 0,
                left: 0,
                display: { xs: 'none', md: 'flex' },
                flexDirection: 'column',
                zIndex: (theme) => theme.zIndex.appBar,
            }}
        >
            <Box sx={{ mt: '64px', flexGrow: 1 }}>
                <List>
                    {menuItems.map((item) => (
                        <ListItem button key={item.text} onClick={() => handleNavigation(item.path)}>
                            <ListItemIcon sx={{ color: '#fff' }}>{item.icon}</ListItemIcon>
                            <ListItemText primary={<Typography sx={{ color: '#fff' }}>{item.text}</Typography>} />
                        </ListItem>
                    ))}
                </List>
                <Button
                    variant="contained"
                    sx={{
                        background: 'linear-gradient(90deg, #F87224, #D9332E)',
                        color: '#fff',
                        borderRadius: 20,
                        width: '100%',
                        mt: 2,
                        '&:hover': {
                            background: 'linear-gradient(90deg, #E69520, #C9302C)',
                        },
                    }}
                    onClick={() => handleNavigation('/home')}
                >
                    Publicar
                </Button>
            </Box>
            <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                        <Typography sx={{ color: '#fff' }}>{userName}</Typography>
                        <Typography variant="body2" sx={{ color: '#aaa' }}>
                            @{userName.toLowerCase().replace(/\s+/g, '')}
                        </Typography>
                    </Box>
                    <IconButton onClick={handleLogout}>
                        <ArrowForward sx={{ color: '#fff' }} />
                    </IconButton>
                </Box>
            </Box>
        </Box>
    );
};

export default Sidebar;