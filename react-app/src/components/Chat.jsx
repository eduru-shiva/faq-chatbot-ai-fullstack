import React, { useState, useContext, useEffect } from 'react'
import { Card, Form, Button, ListGroup, Spinner, Alert } from 'react-bootstrap'
import axios from 'axios'
import { AuthContext } from '../contexts/AuthContext'
import ReactMarkdown from 'react-markdown'

const Chat = ({ selectedFile }) => {
  const { token, pineconeKey } = useContext(AuthContext)
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [noHistoryMessage] = useState('There is no Conversation for this file yet.')

  const fetchHistory = async () => {
    if (!selectedFile) {
      setMessages([])
      return
    }
    try {
      const response = await axios.get(
        `http://localhost:8000/chat/history/${selectedFile.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (response.data.length === 0) {
        setMessages([])
      } else {
        setMessages(response.data)
      }
    } catch (err) {
      console.error('Error fetching history:', err)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [selectedFile])

  const handleSend = async () => {
    if (!query || !selectedFile || !pineconeKey) {
      alert('Please ensure you have selected a file, entered a query, and set your Pinecone API key.')
      return
    }
    setLoading(true)
    try {
      const historyStr = messages.map((m) => `${m.role}: ${m.content}`).join('\n')
      const formData = new FormData()
      formData.append('pinecone_api_key', pineconeKey)
      formData.append('file_id', selectedFile.id)
      formData.append('query', query)
      formData.append('history', historyStr)

      const response = await axios.post(
        'http://localhost:8000/chat/query',
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setMessages((prev) => [
        ...prev,
        { role: 'user', content: query },
        { role: 'assistant', content: response.data.response },
      ])
      setQuery('')
    } catch (err) {
      console.error('Error sending message: ', err)
      alert(err.response?.data.detail || 'Enter the respective Pinecone API you used to store the file')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card
      className="m-3"
      style={{
        height: 'calc(100% - 2rem)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Card.Body style={{ flex: 1, overflowY: 'auto' }}>
        <h5>Chat with: {selectedFile ? selectedFile.file_name : 'No file selected'}</h5>
        {messages.length === 0 ? (
          <Alert variant="info">{noHistoryMessage}</Alert>
        ) : (
          <ListGroup variant="flush">
            {messages.map((msg, index) => {
              const isUser = msg.role === 'user'
              return (
                <ListGroup.Item
                  key={index}
                  style={{
                    textAlign: isUser ? 'right' : 'left',
                    backgroundColor: isUser ? '#d1e7dd' : '#f8d7da',
                    border: 'none',
                    marginBottom: '5px',
                    borderRadius: '10px',
                    padding: '10px',
                  }}
                >
                  <strong>{isUser ? 'You' : 'Bot'}</strong>:{' '}
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </ListGroup.Item>
              )
            })}
          </ListGroup>
        )}
      </Card.Body>
      <Card.Footer>
        <Form onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
          <Form.Group className="d-flex">
            <Form.Control
              type="text"
              placeholder="Type your query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Button variant="primary" type="submit" disabled={loading} className="ms-2">
              {loading ? <Spinner animation="border" size="sm" /> : 'Send'}
            </Button>
          </Form.Group>
        </Form>
      </Card.Footer>
    </Card>
  )
}

export default Chat
