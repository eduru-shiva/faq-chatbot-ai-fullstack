import React, { useState, useEffect, useContext } from 'react'
import { Accordion, Spinner, Alert, Card } from 'react-bootstrap'
import axios from 'axios'
import { AuthContext } from '../contexts/AuthContext'
import ReactMarkdown from 'react-markdown'

const FileList = () => {
  const { token } = useContext(AuthContext)
  const [files, setFiles] = useState([])
  const [fileDetails, setFileDetails] = useState({})
  const [loadingDetails, setLoadingDetails] = useState({})
  const [error, setError] = useState('')

  const fetchFiles = async () => {
    try {
      const response = await axios.get('http://localhost:8000/files', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setFiles(response.data)
    } catch (err) {
      console.error(err)
      setError('Failed to fetch files.')
    }
  }
  
  const fetchFileDetail = async (fileId) => {
    if (fileDetails[fileId]) return;
    setLoadingDetails(prev => ({ ...prev, [fileId]: true }))
    try {
      const response = await axios.get(`http://localhost:8000/files/${fileId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setFileDetails(prev => ({ ...prev, [fileId]: response.data.file_content }))
    } catch (err) {
      console.error(err)
      setFileDetails(prev => ({ ...prev, [fileId]: 'Error fetching details.' }))
    } finally {
      setLoadingDetails(prev => ({ ...prev, [fileId]: false }))
    }
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  return (
    <div className="m-3">
      {error && <Alert variant="danger">{error}</Alert>}
      {files.length === 0 ? (
        <Alert variant="secondary">No files have been uploaded yet.</Alert>
      ) : (
        <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
          <Accordion>
            {files.map(file => (
              <Accordion.Item eventKey={file.id.toString()} key={file.id}>
                <Accordion.Header
                  onClick={() => fetchFileDetail(file.id)}
                >
                  {file.file_name}
                </Accordion.Header>
                <Accordion.Body>
                  {loadingDetails[file.id] ? (
                    <Spinner animation="border" size="sm" />
                  ) : (
                    <Card style={{ height: '300px', overflowY: 'auto' }}>
                      <Card.Body>
                        <ReactMarkdown>
                          {fileDetails[file.id] || 'No content available.'}
                        </ReactMarkdown>
                      </Card.Body>
                    </Card>
                  )}
                </Accordion.Body>
              </Accordion.Item>
            ))}
          </Accordion>
        </div>
      )}
    </div>
  )
}

export default FileList
