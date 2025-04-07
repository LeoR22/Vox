import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TextField, Button, Typography, Box, Container } from '@mui/material';
import axios from 'axios';

const Login = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const API_URL = 'http://localhost:8000';

    const handleRegister = async () => {
        try {
            const response = await axios.post(`${API_URL}/auth/register`, { email, password });
            setMessage(response.data.message);
        } catch (error) {
            setMessage(error.response?.data?.detail || 'Error al registrar');
        }
    };

    const handleLogin = async () => {
        try {
            const response = await axios.post(`${API_URL}/auth/login`, { email, password });
            const token = response.data.access_token;
            let userId;
            let userName;

            try {
                const userResponse = await axios.post(
                    `${API_URL}/users`,
                    { email, name: email.split('@')[0], bio: `Hola, soy ${email.split('@')[0]}` },
                    { headers: { Authorization: `Bearer ${token}` } }
                );
                userId = userResponse.data.user_id;
                userName = userResponse.data.name;
            } catch (error) {
                if (error.response?.status === 400 && error.response?.data?.detail.includes('already exists')) {
                    const usersResponse = await axios.get(`${API_URL}/users`, {
                        headers: { Authorization: `Bearer ${token}` },
                    });
                    const user = usersResponse.data.find((u) => u.email === email);
                    if (user) {
                        userId = user._id;
                        userName = user.name;
                    } else {
                        throw new Error('Usuario no encontrado');
                    }
                } else {
                    throw error;
                }
            }

            console.log('Login Data:', { token, userId, userName }); // Añadimos un log para depurar
            onLogin(token, userId, userName);
            setMessage('Inicio de sesión exitoso');
            navigate('/home');
        } catch (error) {
            setMessage(error.response?.data?.detail || 'Error al iniciar sesión');
        }
    };

    return (
        <Container maxWidth="xs">
            <Box sx={{ mt: 8, textAlign: 'center' }}>
                <Typography variant="h4" color="primary" gutterBottom>
                    Twitter Clone
                </Typography>
                <TextField
                    label="Email"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                <TextField
                    label="Contraseña"
                    type="password"
                    variant="outlined"
                    fullWidth
                    margin="normal"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    sx={{ mt: 2, borderRadius: 20 }}
                    onClick={handleRegister}
                >
                    Registrar
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    fullWidth
                    sx={{ mt: 1, borderRadius: 20 }}
                    onClick={handleLogin}
                >
                    Iniciar Sesión
                </Button>
                {message && (
                    <Typography color="error" sx={{ mt: 2 }}>
                        {message}
                    </Typography>
                )}
            </Box>
        </Container>
    );
};

export default Login;