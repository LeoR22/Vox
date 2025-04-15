import React, { useState, useCallback, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Sidebar from './components/Sidebar';
import Feed from './components/Feed';
import Login from './components/Login';
import Register from './components/Register';
import Profile from './components/Profile';
import Messages from './components/Messages';

const NotImplemented = ({ title }) => (
  <Box sx={{ color: '#fff', textAlign: 'center', mt: 5 }}>
    <h2>{title}</h2>
    <p>Esta funcionalidad está en desarrollo. Vuelve pronto.</p>
  </Box>
);

const NotFound = () => (
  <Box sx={{ color: '#fff', textAlign: 'center', mt: 5 }}>
    <h2>Página no encontrada</h2>
    <p>La ruta solicitada no existe.</p>
  </Box>
);

const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '');
  const [userName, setUserName] = useState(localStorage.getItem('userName') || '');

  const handleLogin = useCallback((newToken, newUserId, newUserName) => {
    console.log('Logging in:', { newToken, newUserId, newUserName });
    setToken(newToken);
    setUserId(newUserId);
    setUserName(newUserName);
    localStorage.setItem('token', newToken);
    localStorage.setItem('userId', newUserId);
    localStorage.setItem('userName', newUserName);
  }, []);

  const handleRegister = useCallback((newUserId, newUserName) => {
    console.log('Registering:', { newUserId, newUserName });
    setUserId(newUserId);
    setUserName(newUserName);
    localStorage.setItem('userId', newUserId);
    localStorage.setItem('userName', newUserName);
  }, []);

  const handleLogout = useCallback(() => {
    console.log('Logging out');
    setToken('');
    setUserId('');
    setUserName('');
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');
  }, []);

  useEffect(() => {
    console.log('App state:', { token: !!token, tokenValue: token, userId, userName });
  }, [token, userId, userName]);

  return (
    <Router>
      <Box sx={{ display: 'flex', bgcolor: '#292A2C', minHeight: '100vh', width: '100%' }}>
        <Routes>
          <Route path="/login" element={<Login onLogin={handleLogin} />} />
          <Route path="/register" element={<Register onRegister={handleRegister} />} />
          <Route
            path="*"
            element={
              token ? (
                <>
                  <Sidebar handleLogout={handleLogout} userName={userName} userId={userId} />
                  <Box sx={{ flex: 1, ml: { xs: 0, md: '275px' }, p: 3, maxWidth: '1200px', mx: 'auto' }}>
                    <Routes>
                      <Route path="/home" element={<Feed token={token} userId={userId} userName={userName} />} />
                      <Route
                        path="/profile/:username"
                        element={<Profile token={token} userId={userId} userName={userName} />}
                      />
                      <Route
                        path="/messages"
                        element={<Messages token={token} userId={userId} userName={userName} />}
                      />
                      <Route path="/explore" element={<NotImplemented title="Explorar" />} />
                      <Route path="/notifications" element={<NotImplemented title="Notificaciones" />} />
                      <Route path="/bookmarks" element={<NotImplemented title="Guardados" />} />
                      <Route path="/lists" element={<NotImplemented title="Listas" />} />
                      <Route path="/more" element={<NotImplemented title="Más Opciones" />} />
                      <Route path="/" element={<Navigate to="/home" replace />} />
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Box>
                </>
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
        </Routes>
      </Box>
    </Router>
  );
};

export default App;