import React, { useState, useEffect } from 'react';
import { Box, Typography, List, ListItem, ListItemText, Paper } from '@mui/material';
import { Notifications as NotificationsIcon } from '@mui/icons-material';
import axios from 'axios';

const Notifications = ({ userId, token }) => {
    const [notifications, setNotifications] = useState([]);
    const [ws, setWs] = useState(null);
    const API_URL = 'http://localhost:8000';

    // Fetch historical notifications on mount
    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                const response = await axios.get(`${API_URL}/notifications/${userId}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setNotifications(response.data);
            } catch (err) {
                console.error('Error fetching notifications:', err);
            }
        };
        fetchNotifications();
    }, [userId, token]);

    // Establish WebSocket connection
    useEffect(() => {
        const websocket = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}`);
        websocket.onopen = () => {
            console.log('WebSocket connected for notifications');
        };
        websocket.onmessage = (event) => {
            const notification = JSON.parse(event.data);
            setNotifications((prev) => [notification, ...prev]);
        };
        websocket.onclose = () => {
            console.log('WebSocket disconnected');
        };
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        setWs(websocket);

        return () => {
            websocket.close();
        };
    }, [userId]);

    return (
        <Paper sx={{ p: 2, bgcolor: '#3a3b3c', color: '#fff', maxWidth: 400, mx: 'auto', mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <NotificationsIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Notificaciones</Typography>
            </Box>
            <List>
                {notifications.map((notif, index) => (
                    <ListItem key={index} sx={{ bgcolor: '#2a2b2c', mb: 1, borderRadius: 1 }}>
                        <ListItemText
                            primary={notif.message}
                            secondary={`${new Date(notif.created_at).toLocaleString()}`}
                            primaryTypographyProps={{ color: '#fff' }}
                            secondaryTypographyProps={{ color: '#aaa' }}
                        />
                    </ListItem>
                ))}
            </List>
        </Paper>
    );
};

export default Notifications;