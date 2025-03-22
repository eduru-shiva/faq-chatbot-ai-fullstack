import React, { useState, useContext } from 'react'
import axios from 'axios'
import { AuthContext } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import {
  Container,
  Card,
  Form,
  Button,
  Alert
} from 'react-bootstrap'
import { FaRobot } from 'react-icons/fa'

const Auth = () => {
  const [isSignup, setIsSignup] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (isSignup) {
        await axios.post('http://localhost:8000/signup', { username, password })
        alert('Signup successful. Please login.')
        setIsSignup(false)
      } else {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)
        const response = await axios.post('http://localhost:8000/login', formData)
        login(response.data.access_token, { username })
        navigate('/')
      }
    } catch (err) {
      setError(err.response?.data.detail || 'An error occurred')
    }
  }

  return (
    <Container
      fluid
      className="d-flex flex-column align-items-center justify-content-center bg-light"
      style={{ height: '100vh' }}
    >
      
      <div className="text-center mb-4">
        <h1 className="d-flex align-items-center justify-content-center">
          <FaRobot className="me-2" /> FAQ ChatBot AI
        </h1>
      </div>

      <Card style={{ width: '400px' }}>
        <Card.Body>
          <Card.Title className="text-center mb-4">
            {isSignup ? 'Signup' : 'Login'}
          </Card.Title>

          {error && <Alert variant="danger">{error}</Alert>}

          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="formUsername">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Form.Group>

            <Button variant="primary" type="submit" className="w-100">
              {isSignup ? 'Signup' : 'Login'}
            </Button>
          </Form>

          <div className="text-center mt-3">
            <Button
              variant="link"
              onClick={() => setIsSignup(!isSignup)}
            >
              {isSignup
                ? 'Already have an account? Login'
                : "Don't have an account? Signup"}
            </Button>
          </div>
        </Card.Body>
      </Card>
    </Container>
  )
}

export default Auth
