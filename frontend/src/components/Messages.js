import React, { useState, useEffect, useRef } from 'react';
import {
    Box,
    Typography,
    TextField,
    Button,
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Avatar,
    CircularProgress,
} from '@mui/material';
import { Send } from '@mui/icons-material';
import axios from 'axios';

const Messages = ({ token, userId, userName }) => {
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [ws, setWs] = useState(null);
    const API_URL = 'http://localhost:8000';
    const messagesEndRef = useRef(null);

    // Fetch users
    const fetchUsers = async () => {
        try {
            const response = await axios.get(`${API_URL}/users`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            const filteredUsers = response.data.filter((user) => user.user_id !== userId);
            setUsers(filteredUsers);
            setLoading(false);
        } catch (error) {
            setError('Error al obtener usuarios: ' + (error.response?.data?.detail || error.message));
            setLoading(false);
        }
    };

    // Fetch messages between two users
    const fetchMessages = async (receiverId) => {
        try {
            const response = await axios.get(
                `${API_URL}/chat/messages/${userId}/${receiverId}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            setMessages(response.data);
        } catch (error) {
            setError('Error al obtener mensajes: ' + (error.response?.data?.detail || error.message));
        }
    };

    // Initialize WebSocket
    const initializeWebSocket = () => {
        const websocket = new WebSocket(`ws://localhost:8007/ws/chat/${userId}`);
        websocket.onopen = () => {
            websocket.send(`Bearer ${token}`);
        };
        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.status === 'connected') {
                    console.log('WebSocket connected:', data);
                } else {
                    setMessages((prev) => [...prev, data]);
                    scrollToBottom();
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        websocket.onclose = () => {
            console.log('WebSocket disconnected');
        };
        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            setError('Error en la conexión de mensajes en tiempo real');
        };
        setWs(websocket);
        return () => websocket.close();
    };

    // Scroll to bottom of messages
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Handle user selection
    const handleSelectUser = (user) => {
        setSelectedUser(user);
        setMessages([]);
        fetchMessages(user.user_id);
    };

    // Send message
    const handleSendMessage = async () => {
        if (!newMessage.trim() || !selectedUser) return;
        const message = {
            sender_id: userId,
            receiver_id: selectedUser.user_id,
            content: newMessage,
        };
        try {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(message));
                setMessages((prev) => [...prev, { ...message, created_at: new Date() }]);
                setNewMessage('');
                scrollToBottom();
            } else {
                await axios.post(
                    `${API_URL}/chat/messages`,
                    message,
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                setNewMessage('');
                fetchMessages(selectedUser.user_id);
            }
        } catch (error) {
            setError('Error al enviar mensaje: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchUsers();
        const cleanup = initializeWebSocket();
        return cleanup;
    }, [token, userId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <Box sx={{ display: 'flex', p: 3, maxWidth: '1200px', mx: 'auto', gap: 3 }}>
            {/* Lista de usuarios */}
            <Box sx={{ width: '300px', bgcolor: '#3a3b3c', borderRadius: 2, p: 2 }}>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                    Chats
                </Typography>
                {loading ? (
                    <CircularProgress sx={{ color: '#fff' }} />
                ) : error ? (
                    <Typography sx={{ color: '#ff4d4f' }}>{error}</Typography>
                ) : users.length === 0 ? (
                    <Typography sx={{ color: '#fff' }}>No hay usuarios disponibles</Typography>
                ) : (
                    <List>
                        {users.map((user) => (
                            <ListItem
                                button
                                key={user.user_id}
                                onClick={() => handleSelectUser(user)}
                                sx={{
                                    bgcolor: selectedUser?.user_id === user.user_id ? '#4a4b4c' : 'transparent',
                                    borderRadius: 1,
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
                                        <Typography sx={{ color: '#aaa' }}>@{user.user_id}</Typography>
                                    }
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Box>

            {/* Área de chat */}
            <Box sx={{ flex: 1, bgcolor: '#3a3b3c', borderRadius: 2, p: 2, display: 'flex', flexDirection: 'column' }}>
                {selectedUser ? (
                    <>
                        <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                            {selectedUser.name} (@{selectedUser.user_id})
                        </Typography>
                        <Box
                            sx={{
                                flex: 1,
                                overflowY: 'auto',
                                mb: 2,
                                maxHeight: '500px',
                                '&::-webkit-scrollbar': { width: '8px' },
                                '&::-webkit-scrollbar-thumb': { bgcolor: '#4a4b4c', borderRadius: '4px' },
                            }}
                        >
                            {messages.length === 0 ? (
                                <Typography sx={{ color: '#fff', textAlign: 'center' }}>
                                    No hay mensajes
                                </Typography>
                            ) : (
                                messages.map((msg, index) => (
                                    <Box
                                        key={index}
                                        sx={{
                                            display: 'flex',
                                            justifyContent: msg.sender_id === userId ? 'flex-end' : 'flex-start',
                                            mb: 1,
                                        }}
                                    >
                                        <Box
                                            sx={{
                                                maxWidth: '60%',
                                                bgcolor: msg.sender_id === userId ? '#F87224' : '#4a4b4c',
                                                color: '#fff',
                                                p: 1,
                                                borderRadius: 2,
                                            }}
                                        >
                                            <Typography>{msg.content}</Typography>
                                            <Typography variant="caption" sx={{ color: '#ddd' }}>
                                                {new Date(msg.created_at).toLocaleTimeString()}
                                            </Typography>
                                        </Box>
                                    </Box>
                                ))
                            )}
                            <div ref={messagesEndRef} />
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                            <TextField
                                placeholder="Escribe un mensaje..."
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                fullWidth
                                size="small"
                                sx={{
                                    bgcolor: '#4a4b4c',
                                    borderRadius: 1,
                                    input: { color: '#fff' },
                                    '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                                }}
                            />
                            <Button
                                onClick={handleSendMessage}
                                variant="contained"
                                sx={{
                                    background: 'linear-gradient(90deg, #F87224, #D9332E)',
                                    borderRadius: 20,
                                }}
                            >
                                <Send />
                            </Button>
                        </Box>
                    </>
                ) : (
                    <Typography sx={{ color: '#fff', textAlign: 'center', mt: 5 }}>
                        Selecciona un usuario para chatear
                    </Typography>
                )}
            </Box>
        </Box>
    );
};

export default Messages;