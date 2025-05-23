import React, { useState } from 'react';
import { Box, TextField, Button, Typography, IconButton } from '@mui/material';
import { Facebook } from '@mui/icons-material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const API_URL = 'http://localhost:8000';

    const handleLogin = async () => {
        console.log('Intentando iniciar sesión con:', { email, password });
        try {
            const response = await axios.post(`${API_URL}/auth/login`, { email, password });
            console.log('Respuesta del login:', response.data);
            const { token, user_id, name } = response.data;
            // Almacenar token y user_id en localStorage
            localStorage.setItem('token', token);
            localStorage.setItem('user_id', user_id);
            localStorage.setItem('name', name);
            onLogin(token, user_id, name);
            navigate('/home'); // Redirigir a /home tras login exitoso
        } catch (error) {
            console.error('Error completo:', error);
            setError('Error al iniciar sesión: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleFacebookLogin = () => {
        setError('Inicio de sesión con Facebook no implementado');
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
                        Inicia sesión en Vox
                    </Typography>
                </Box>
                <TextField
                    label="Teléfono, correo electrónico"
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
                    onClick={handleLogin}
                >
                    Siguiente
                </Button>
                <Typography variant="body2" sx={{ color: '#fff', mb: 2 }}>
                    ¿Olvidaste tu contraseña?
                </Typography>
                <Typography variant="body2" sx={{ color: '#fff', mb: 2 }}>
                    ¿No tienes una cuenta?{' '}
                    <span
                        style={{ color: '#f5a623', cursor: 'pointer', textDecoration: 'underline' }}
                        onClick={() => navigate('/register')}
                    >
                        Regístrate
                    </span>
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                    <IconButton onClick={handleFacebookLogin}>
                        <Facebook sx={{ color: '#3b5998' }} />
                    </IconButton>
                </Box>
                {error && (
                    <Typography color="error" sx={{ mt: 2 }}>
                        {error}
                    </Typography>
                )}
            </Box>
        </Box>
    );
};

export default Login;