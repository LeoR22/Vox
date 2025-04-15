import React, { useState, useEffect } from 'react';
import { Box, Typography, TextField, Button, List, ListItem, ListItemText } from '@mui/material';
import axios from 'axios';

const Chat = ({ token, userId }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [receiverId, setReceiverId] = useState('');
    const [ws, setWs] = useState(null);
    const [messageError, setMessageError] = useState('');

    const API_URL = 'http://localhost:8000';

    const fetchMessages = async () => {
        if (!receiverId) {
            setMessageError('Por favor, ingresa un ID de receptor');
            return;
        }
        try {
            const response = await axios.get(`${API_URL}/chat/messages/${userId}/${receiverId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setMessages(response.data);
            setMessageError('');
        } catch (error) {
            setMessageError('Error al obtener mensajes: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        const websocket = new WebSocket(`ws://localhost:8000/ws/chat/${userId}`);
        websocket.onopen = () => {
            websocket.send(`Bearer ${token}`);
            setMessageError(''); // Limpiamos el mensaje de error si la conexión es exitosa
        };
        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setMessages((prev) => [...prev, data]);
        };
        websocket.onerror = (error) => {
            setMessageError('Error en WebSocket: ' + error.message);
        };
        websocket.onclose = () => {
            setMessageError('Conexión WebSocket cerrada');
        };
        setWs(websocket);
        return () => websocket.close();
    }, [userId, token]);

    const handleSendMessage = () => {
        if (!receiverId) {
            setMessageError('Por favor, ingresa un ID de receptor');
            return;
        }
        if (!newMessage.trim()) {
            setMessageError('El mensaje no puede estar vacío');
            return;
        }
        if (ws && ws.readyState === WebSocket.OPEN) {
            const messageData = {
                sender_id: userId,
                receiver_id: receiverId,
                content: newMessage,
            };
            ws.send(JSON.stringify(messageData));
            setNewMessage('');
            setMessageError('');
        } else {
            setMessageError('WebSocket no está conectado');
        }
    };

    return (
        <Box sx={{ width: 300, p: 2, bgcolor: '#000', color: '#fff' }}>
            <Typography variant="h6">Chat</Typography>
            <TextField
                fullWidth
                placeholder="ID del receptor"
                value={receiverId}
                onChange={(e) => setReceiverId(e.target.value)}
                variant="outlined"
                size="small"
                sx={{ mt: 1, bgcolor: '#fff' }}
            />
            <Button
                variant="contained"
                color="primary"
                fullWidth
                sx={{ mt: 1, borderRadius: 20 }}
                onClick={fetchMessages}
            >
                Cargar Mensajes
            </Button>
            <Box sx={{ mt: 2, maxHeight: 300, overflowY: 'auto' }}>
                {messages.length === 0 ? (
                    <Typography>No hay mensajes</Typography>
                ) : (
                    <List>
                        {messages.map((msg) => (
                            <ListItem key={msg._id}>
                                <ListItemText
                                    primary={msg.content}
                                    secondary={msg.sender_id === userId ? 'Tú' : msg.sender_id}
                                    sx={{
                                        bgcolor: msg.sender_id === userId ? '#e3f2fd' : '#f5f5f5',
                                        p: 1,
                                        borderRadius: 2,
                                        mb: 1,
                                    }}
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Box>
            <TextField
                fullWidth
                placeholder="Escribe un mensaje..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                variant="outlined"
                size="small"
                sx={{ mt: 1, bgcolor: '#fff' }}
            />
            <Button
                variant="contained"
                color="primary"
                fullWidth
                sx={{ mt: 1, borderRadius: 20 }}
                onClick={handleSendMessage}
            >
                Enviar
            </Button>
            {messageError && (
                <Typography color="error" sx={{ mt: 2 }}>
                    {messageError}
                </Typography>
            )}
        </Box>
    );
};

export default Chat;