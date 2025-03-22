import React, { createContext, useState } from 'react'

export const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [pineconeKey, setPineconeKey] = useState("")

  const login = (accessToken, userData) => {
    setToken(accessToken)
    setUser(userData)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    setPineconeKey("")  
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, pineconeKey, setPineconeKey }}>
      {children}
    </AuthContext.Provider>
  )
}
