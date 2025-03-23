import React, { useState, useContext, useEffect } from 'react'
import { Form, Button, ListGroup, Card, Alert, Spinner } from 'react-bootstrap'
import axios from 'axios'
import { AuthContext } from '../contexts/AuthContext'

const Sidebar = ({ setSelectedFile, selectedFile }) => {
  const { token, pineconeKey, setPineconeKey } = useContext(AuthContext)
  const [fileName, setFileName] = useState('')
  const [fileData, setFileData] = useState(null)
  const [files, setFiles] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:8000/files', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setFiles(response.data)
    } catch (err) {
      console.error(err)
      setMessage('Failed to fetch files.')
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  const handleUpload = async () => {
    if (!fileData || !fileName || !pineconeKey) {
      setMessage('Please fill all fields.')
      return
    }
    const formData = new FormData()
    formData.append('pinecone_api_key', pineconeKey)
    formData.append('file_name', fileName)
    formData.append('file', fileData)

    try {
      setLoading(true)
      setMessage('')
      await axios.post('http://localhost:8000/files/upload', formData, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setMessage('File uploaded successfully.')
      setFileName('')
      setFileData(null)
      fetchFiles()
    } catch (err) {
      setMessage(err.response?.data.detail || 'Upload failed, either the file is too large or the API key is invalid, or there is no space left in your Pinecone account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="m-3" style={{ border: 'none' }}>
      <Card.Body>
        <Card.Title>Pinecone API Key</Card.Title>
        <Form.Group className="mb-3">
          <Form.Control
            type="text"
            placeholder="Enter API key"
            value={pineconeKey}
            onChange={(e) => setPineconeKey(e.target.value)}
          />
        </Form.Group>
        <hr />
        <Card.Title>Upload File</Card.Title>
        <Form.Group className="mb-3">
          <Form.Control
            type="text"
            placeholder="Enter File Name"
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Control type="file" onChange={(e) => setFileData(e.target.files[0])} />
        </Form.Group>
        <Button
          variant="primary"
          onClick={handleUpload}
          className="w-100 mb-3"
          disabled={loading}
        >
          {loading ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              Uploading...
            </>
          ) : (
            'Upload File'
          )}
        </Button>
        {message && <Alert variant="info">{message}</Alert>}
        <hr />
        <Card.Title>Your Files</Card.Title>
        {files.length === 0 ? (
          <Alert variant="secondary">No files have been uploaded yet.</Alert>
        ) : (
          <ListGroup>
            {files.map((file) => (
              <ListGroup.Item
                key={file.id}
                action
                active={selectedFile && selectedFile.id === file.id}
                onClick={() => setSelectedFile(file)}
              >
                {file.file_name}
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </Card.Body>
    </Card>
  )
}

export default Sidebar
