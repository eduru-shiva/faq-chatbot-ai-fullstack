import React, { useContext } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Auth from './components/Auth'
import Main from './components/Main'
import { AuthContext } from './contexts/AuthContext'

const App = () => {
  const { token } = useContext(AuthContext)

  return (
    <Routes>
      <Route path="/login" element={<Auth />} />
      <Route path="/*" element={token ? <Main /> : <Navigate to="/login" />} />
    </Routes>
  )
}

export default App
