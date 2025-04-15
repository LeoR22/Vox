import React, { useState, useEffect } from 'react';
import { Box, Typography, TextField, Button, Paper } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';

const Messages = ({ token, userId, userName }) => {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [recipientId, setRecipientId] = useState('');
    const [message, setMessage] = useState('');

    const API_URL = 'http://localhost:8000';

    const fetchMessages = async () => {
        try {
            const response = await axios.get(`${API_URL}/messages`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { user_id: userId },
            });
            setMessages(response.data);
        } catch (error) {
            setMessage('Error al obtener mensajes: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleSendMessage = async () => {
        if (!newMessage.trim() || !recipientId) {
            setMessage('El mensaje y el destinatario no pueden estar vacíos');
            return;
        }
        try {
            await axios.post(
                `${API_URL}/messages`,
                { sender_id: userId, recipient_id: recipientId, content: newMessage },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setNewMessage('');
            setRecipientId('');
            setMessage('Mensaje enviado con éxito');
            fetchMessages();
        } catch (error) {
            setMessage('Error al enviar mensaje: ' + (error.response?.data?.detail || error.message));
        }
    };

    useEffect(() => {
        fetchMessages();
    }, [userId, token]);

    return (
        <Box sx={{ display: 'flex', gap: 3 }}>
            {/* Sección principal (mensajes) */}
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
                    <Typography variant="h6">Mensajes</Typography>
                    <TextField
                        placeholder="ID del destinatario"
                        value={recipientId}
                        onChange={(e) => setRecipientId(e.target.value)}
                        fullWidth
                        variant="outlined"
                        size="small"
                        sx={{
                            bgcolor: '#2a2b2c',
                            borderRadius: 2,
                            input: { color: '#fff' },
                            '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                            mb: 2,
                        }}
                    />
                    <TextField
                        placeholder="Escribe un mensaje"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        fullWidth
                        multiline
                        rows={3}
                        variant="outlined"
                        sx={{
                            bgcolor: '#2a2b2c',
                            borderRadius: 2,
                            input: { color: '#fff' },
                            '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                            mb: 2,
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
                        onClick={handleSendMessage}
                    >
                        Enviar
                    </Button>
                </Paper>
                {message && (
                    <Typography color={message.includes('éxito') ? '#f5a623' : 'error'} sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                )}
                {messages.length === 0 ? (
                    <Typography sx={{ color: '#fff' }}>No hay mensajes</Typography>
                ) : (
                    messages.map((msg) => (
                        <Paper key={msg._id} sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
                            <Typography variant="subtitle2">
                                {msg.sender_id === userId ? 'Tú' : msg.sender_id} para {msg.recipient_id === userId ? 'Tú' : msg.recipient_id}
                            </Typography>
                            <Typography>{msg.content}</Typography>
                        </Paper>
                    ))
                )}
            </Box>

            {/* Sección de tendencias y sugerencias */}
            <Box sx={{ flex: 1, maxWidth: '350px' }}>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                    Qué está sucediendo
                </Typography>
                <Paper sx={{ p: 2, mb: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
                    <Typography>[Placeholder para tendencias]</Typography>
                </Paper>
                <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                    A quién seguir
                </Typography>
                <TextField
                    placeholder="Buscar usuarios"
                    variant="outlined"
                    size="small"
                    sx={{
                        bgcolor: '#3a3b3c',
                        borderRadius: 5,
                        input: { color: '#fff' },
                        '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
                        width: '100%',
                        mb: 2,
                    }}
                    InputProps={{
                        startAdornment: <SearchIcon sx={{ color: '#fff', mr: 1 }} />,
                    }}
                />
                <Paper sx={{ p: 2, bgcolor: '#3a3b3c', color: '#fff' }}>
                    <Typography>[Placeholder para usuarios]</Typography>
                </Paper>
            </Box>
        </Box>
    );
};

export default Messages;