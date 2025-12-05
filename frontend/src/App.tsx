import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import BasicLayout from './layouts/BasicLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Nodes from './pages/Nodes'
import Datasets from './pages/Datasets'
import Jobs from './pages/Jobs'
import Users from './pages/Users'
import Files from './pages/Files'
import Settings from './pages/Settings'
import Projects from './pages/Projects'
import ProjectEditor from './pages/Projects/components/ProjectEditor'
import Profile from './pages/Profile'
import { getToken } from './utils/auth'
import { NodeProvider } from './contexts/NodeContext'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!getToken())

  useEffect(() => {
    const token = getToken()
    setIsAuthenticated(!!token)
  }, [])

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={() => setIsAuthenticated(true)} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <NodeProvider>
      <Routes>
        <Route path="/" element={<BasicLayout onLogout={() => setIsAuthenticated(false)} />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="nodes" element={<Nodes />} />
          <Route path="datasets" element={<Datasets />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="files" element={<Files />} />
          <Route path="users" element={<Users />} />
          <Route path="settings" element={<Settings />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:projectId/editor" element={<ProjectEditor />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </NodeProvider>
  )
}

export default App
