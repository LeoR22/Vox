import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'; // Eliminamos useNavigate
import Login from './components/Login';
import Feed from './components/Feed';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';
import { Box, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import TwitterIcon from '@mui/icons-material/Twitter';

function App() {
  const [token, setToken] = useState(null);
  const [userId, setUserId] = useState(null);
  const [userName, setUserName] = useState(''); // Aseguramos que userName tenga un valor inicial

  const handleLogin = (newToken, newUserId, name) => {
    setToken(newToken);
    setUserId(newUserId);
    setUserName(name || 'Usuario'); // Aseguramos que name no sea undefined
  };

  const handleLogout = () => {
    setToken(null);
    setUserId(null);
    setUserName('');
    window.location.href = '/';
  };

  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" sx={{ bgcolor: '#1da1f2' }}>
          <Toolbar>
            <IconButton edge="start" color="inherit" aria-label="menu">
              <TwitterIcon />
            </IconButton>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              Twitter Clone
            </Typography>
          </Toolbar>
        </AppBar>
        <Routes>
          <Route path="/" element={<Login onLogin={handleLogin} />} />
          <Route
            path="/home"
            element={
              token && userId ? (
                <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                  <Sidebar
                    token={token}
                    userId={userId}
                    userName={userName}
                    onLogout={handleLogout}
                  />
                  <Feed token={token} userId={userId} />
                  <Chat token={token} userId={userId} />
                </Box>
              ) : (
                <Login onLogin={handleLogin} />
              )
            }
          />
        </Routes>
      </Box>
    </Router>
  );
}

export default App;