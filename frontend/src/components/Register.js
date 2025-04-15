import React, { useState } from 'react';
import { Box, TextField, Button, Typography } from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Register = ({ onRegister }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [bio, setBio] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const API_URL = 'http://localhost:8000';

    const handleRegister = async () => {
        try {
            const response = await axios.post(`${API_URL}/users`, {
                email,
                password,
                name,
                bio,
                user_id: email.split('@')[0], // Esto está bien para generar user_id
            });
            setMessage('Registro exitoso. Por favor, inicia sesión.');
            onRegister(response.data.user_id, name);
            setTimeout(() => navigate('/'), 2000); // Redirige a login tras 2 segundos
        } catch (error) {
            console.error('Error al registrarse:', error);
            setMessage(
                'Error al registrarse: ' +
                (error.response?.data?.detail || error.message)
            );
        }
    };

    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                height: '100vh',
                width: '100vw',
                position: 'fixed',
                top: 0,
                left: 0,
                backgroundImage: 'url(/background.jpg)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
            }}
        >
            <Box
                sx={{
                    bgcolor: '#333',
                    p: 4,
                    borderRadius: 2,
                    width: 400,
                    textAlign: 'center',
                }}
            >
                <Box sx={{ mb: 2 }}>
                    <img
                        src="/logo-1.png"
                        alt="Vox Logo"
                        style={{ width: '50px', height: '50px', marginBottom: '8px' }}
                    />
                    <Typography variant="h5" sx={{ mb: 2, color: '#fff' }}>
                        Regístrate en Vox
                    </Typography>
                </Box>
                <TextField
                    label="Correo electrónico"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    fullWidth
                    sx={{ mb: 2, bgcolor: '#fff' }}
                />
                <TextField
                    label="Contraseña"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    fullWidth
                    sx={{ mb: 2, bgcolor: '#fff' }}
                />
                <TextField
                    label="Nombre"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    fullWidth
                    sx={{ mb: 2, bgcolor: '#fff' }}
                />
                <TextField
                    label="Biografía"
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    fullWidth
                    multiline
                    minRows={2}
                    sx={{ mb: 2, bgcolor: '#fff' }}
                />
                <Button
                    variant="contained"
                    sx={{
                        background: 'linear-gradient(90deg, #F87224, #D9332E)',
                        color: '#fff',
                        borderRadius: 20,
                        mb: 2,
                        width: '100%',
                        '&:hover': {
                            background: 'linear-gradient(90deg, #E69520, #C9302C)',
                        },
                    }}
                    onClick={handleRegister}
                >
                    Siguiente
                </Button>
                {message && (
                    <Typography sx={{ mt: 2, color: message.includes('exitoso') ? '#fff' : 'error.main' }}>
                        {message}
                    </Typography>
                )}
                <Typography variant="body2" sx={{ color: '#fff', mt: 2 }}>
                    ¿Ya tienes una cuenta?{' '}
                    <span
                        style={{ color: '#f5a623', cursor: 'pointer' }}
                        onClick={() => navigate('/')}
                    >
                        Inicia sesión
                    </span>
                </Typography>
            </Box>
        </Box>
    );
};

export default Register;