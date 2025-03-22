import React, { useContext } from 'react'
import { Container, Row, Col, Nav, Tab, Navbar, Button } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'
import Sidebar from './Sidebar'
import Chat from './Chat'
import FileList from './FileList'
import { AuthContext } from '../contexts/AuthContext'
import { FaRobot } from 'react-icons/fa'

const Main = () => {
  const [selectedFile, setSelectedFile] = React.useState(null)
  const { logout, user } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Container
      fluid
      className="p-0"
      style={{
        height: '100vh',     
        overflow: 'hidden',  
      }}
    >
      <Navbar bg="primary" variant="dark">
        <Navbar.Brand className="ms-3 d-flex align-items-center">
          <FaRobot className="me-2" />
          FAQ Chatbot AI
        </Navbar.Brand>
        <Navbar.Collapse className="justify-content-end me-3">
          <div className="text-white me-3">
            {user?.username ? `Hello, ${user.username}` : ''}
          </div>
          <Button variant="outline-light" onClick={handleLogout}>
            Logout
          </Button>
        </Navbar.Collapse>
      </Navbar>

      <Row
        noGutters
        style={{
          height: 'calc(100vh - 56px)', 
          width: '100%',
          margin: 0,
        }}
      >
        <Col
          md={3}
          style={{
            backgroundColor: '#e3f2fd',
            overflowY: 'auto',  
            height: '100%',
          }}
        >
          <Sidebar setSelectedFile={setSelectedFile} selectedFile={selectedFile} />
        </Col>
        <Col
          md={9}
          style={{
            overflow: 'hidden', 
            height: '100%',
          }}
        >
          <Tab.Container defaultActiveKey="chat">
            <Nav variant="tabs" className="justify-content-center mt-3">
              <Nav.Item>
                <Nav.Link eventKey="chat">Chat</Nav.Link>
              </Nav.Item>
              <Nav.Item>
                <Nav.Link eventKey="files">Uploaded Files</Nav.Link>
              </Nav.Item>
            </Nav>
            <Tab.Content style={{ height: 'calc(100% - 3rem)' }}>
              <Tab.Pane eventKey="chat" style={{ height: '100%' }}>
                <Chat selectedFile={selectedFile} />
              </Tab.Pane>
              <Tab.Pane eventKey="files" style={{ height: '100%' }}>
                <FileList />
              </Tab.Pane>
            </Tab.Content>
          </Tab.Container>
        </Col>
      </Row>
    </Container>
  )
}

export default Main
