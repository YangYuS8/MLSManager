import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout,
  Tree,
  Button,
  Space,
  Spin,
  message,
  Typography,
  Breadcrumb,
  Modal,
  Input,
  Tag,
  Tooltip,
  Empty,
} from 'antd'
import type { DataNode, DirectoryTreeProps } from 'antd/es/tree'
import {
  FileOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  SaveOutlined,
  ArrowLeftOutlined,
  SyncOutlined,
  CloudDownloadOutlined,
  CloudUploadOutlined,
  BranchesOutlined,
} from '@ant-design/icons'
import Editor from '@monaco-editor/react'
import { useTranslation } from 'react-i18next'
import { getToken } from '../../../utils/auth'

const { Sider, Content } = Layout
const { Title, Text } = Typography
const { DirectoryTree } = Tree

interface FileInfo {
  name: string
  path: string
  is_dir: boolean
  size: number | null
  modified: string | null
}

interface Project {
  id: number
  name: string
  git_url: string | null
  git_branch: string
  local_path: string
  status: string
}

interface GitStatus {
  current_branch: string
  is_clean: boolean
  modified_files: string[]
  untracked_files: string[]
}

// Helper to get file language for Monaco
const getLanguageFromPath = (path: string): string => {
  const ext = path.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    py: 'python',
    json: 'json',
    html: 'html',
    htm: 'html',
    css: 'css',
    scss: 'scss',
    less: 'less',
    md: 'markdown',
    yaml: 'yaml',
    yml: 'yaml',
    xml: 'xml',
    sql: 'sql',
    sh: 'shell',
    bash: 'shell',
    dockerfile: 'dockerfile',
    c: 'c',
    cpp: 'cpp',
    h: 'cpp',
    java: 'java',
    go: 'go',
    rs: 'rust',
    rb: 'ruby',
    php: 'php',
    swift: 'swift',
    kt: 'kotlin',
  }
  return languageMap[ext || ''] || 'plaintext'
}

const ProjectEditor: React.FC = () => {
  const { t } = useTranslation()
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  
  const [project, setProject] = useState<Project | null>(null)
  const [files, setFiles] = useState<FileInfo[]>([])
  const [treeData, setTreeData] = useState<DataNode[]>([])
  const [loading, setLoading] = useState(true)
  const [fileLoading, setFileLoading] = useState(false)
  const [currentPath, setCurrentPath] = useState<string | null>(null)
  const [currentContent, setCurrentContent] = useState<string>('')
  const [originalContent, setOriginalContent] = useState<string>('')
  const [hasChanges, setHasChanges] = useState(false)
  const [saving, setSaving] = useState(false)
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null)
  const [commitModalVisible, setCommitModalVisible] = useState(false)
  const [commitMessage, setCommitMessage] = useState('')
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([])
  const editorRef = useRef<unknown>(null)

  const fetchProject = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (response.ok) {
        const data = await response.json()
        setProject(data)
      }
    } catch (err) {
      console.error('Failed to fetch project:', err)
    }
  }, [projectId])

  const fetchFiles = useCallback(async (path: string = '') => {
    try {
      const url = `/api/v1/projects/${projectId}/files?path=${encodeURIComponent(path)}`
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (response.ok) {
        return await response.json() as FileInfo[]
      }
      return []
    } catch (err) {
      console.error('Failed to fetch files:', err)
      return []
    }
  }, [projectId])

  const fetchGitStatus = useCallback(async () => {
    if (!project?.git_url) return
    try {
      const response = await fetch(`/api/v1/projects/${projectId}/git/status`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (response.ok) {
        const data = await response.json()
        setGitStatus(data)
      }
    } catch (err) {
      console.error('Failed to fetch git status:', err)
    }
  }, [projectId, project?.git_url])

  const buildTreeData = useCallback((fileList: FileInfo[], parentPath: string = ''): DataNode[] => {
    return fileList.map((file) => ({
      key: file.path,
      title: file.name,
      icon: file.is_dir ? <FolderOutlined /> : <FileOutlined />,
      isLeaf: !file.is_dir,
      children: file.is_dir ? [] : undefined,
    }))
  }, [])

  const loadInitialFiles = useCallback(async () => {
    setLoading(true)
    const rootFiles = await fetchFiles('')
    setFiles(rootFiles)
    setTreeData(buildTreeData(rootFiles))
    setLoading(false)
  }, [fetchFiles, buildTreeData])

  useEffect(() => {
    fetchProject()
    loadInitialFiles()
  }, [fetchProject, loadInitialFiles])

  useEffect(() => {
    if (project) {
      fetchGitStatus()
    }
  }, [project, fetchGitStatus])

  const onLoadData = async (node: DataNode) => {
    const children = await fetchFiles(node.key as string)
    
    setTreeData((origin) => {
      const updateTreeData = (list: DataNode[], key: React.Key, children: DataNode[]): DataNode[] =>
        list.map((node) => {
          if (node.key === key) {
            return { ...node, children }
          }
          if (node.children) {
            return { ...node, children: updateTreeData(node.children, key, children) }
          }
          return node
        })
      return updateTreeData(origin, node.key, buildTreeData(children, node.key as string))
    })
  }

  const onSelect: DirectoryTreeProps['onSelect'] = async (selectedKeys, info) => {
    if (!info.node.isLeaf) return
    
    const path = selectedKeys[0] as string
    
    // Check for unsaved changes
    if (hasChanges) {
      Modal.confirm({
        title: t('common.warning'),
        content: t('projects.editor.unsavedChanges'),
        onOk: () => loadFile(path),
      })
      return
    }
    
    loadFile(path)
  }

  const loadFile = async (path: string) => {
    setFileLoading(true)
    try {
      const response = await fetch(
        `/api/v1/projects/${projectId}/files/content?path=${encodeURIComponent(path)}`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      )
      if (response.ok) {
        const data = await response.json()
        setCurrentPath(path)
        setCurrentContent(data.content)
        setOriginalContent(data.content)
        setHasChanges(false)
      }
    } catch (err) {
      message.error(t('files.readFailed'))
    } finally {
      setFileLoading(false)
    }
  }

  const handleEditorChange = (value: string | undefined) => {
    const newContent = value || ''
    setCurrentContent(newContent)
    setHasChanges(newContent !== originalContent)
  }

  const handleSave = async (withCommit: boolean = false) => {
    if (!currentPath) return
    
    setSaving(true)
    try {
      const body: Record<string, string> = {
        content: currentContent,
      }
      if (withCommit && commitMessage) {
        body.commit_message = commitMessage
      }
      
      const response = await fetch(
        `/api/v1/projects/${projectId}/files/content?path=${encodeURIComponent(currentPath)}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`,
          },
          body: JSON.stringify(body),
        }
      )
      
      if (response.ok) {
        message.success(t('projects.saveSuccess'))
        setOriginalContent(currentContent)
        setHasChanges(false)
        setCommitModalVisible(false)
        setCommitMessage('')
        if (withCommit) {
          fetchGitStatus()
        }
      } else {
        message.error(t('projects.saveFailed'))
      }
    } catch (err) {
      message.error(t('projects.saveFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handlePull = async () => {
    try {
      const response = await fetch(`/api/v1/projects/${projectId}/git/pull`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (response.ok) {
        message.success(t('projects.pullSuccess'))
        loadInitialFiles()
        if (currentPath) {
          loadFile(currentPath)
        }
        fetchGitStatus()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.pullFailed'))
      }
    } catch (err) {
      message.error(t('projects.pullFailed'))
    }
  }

  const handlePush = async () => {
    try {
      const response = await fetch(`/api/v1/projects/${projectId}/git/push`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (response.ok) {
        message.success(t('projects.pushSuccess'))
        fetchGitStatus()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.pushFailed'))
      }
    } catch (err) {
      message.error(t('projects.pushFailed'))
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <Layout className="h-[calc(100vh-120px)]">
      <Sider width={280} theme="light" className="border-r overflow-auto">
        <div className="p-3 border-b">
          <Space direction="vertical" className="w-full">
            <div className="flex items-center justify-between">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/projects')}
                size="small"
              >
                {t('files.back')}
              </Button>
              <Button icon={<SyncOutlined />} size="small" onClick={loadInitialFiles} />
            </div>
            <Title level={5} className="m-0 truncate" title={project?.name}>
              {project?.name}
            </Title>
            {gitStatus && (
              <Space size="small" wrap>
                <Tag icon={<BranchesOutlined />}>{gitStatus.current_branch}</Tag>
                {gitStatus.is_clean ? (
                  <Tag color="green">{t('projects.noChanges')}</Tag>
                ) : (
                  <Tag color="orange">{t('projects.hasChanges')}</Tag>
                )}
              </Space>
            )}
          </Space>
        </div>
        <div className="p-2">
          <Text type="secondary" className="text-xs mb-2 block">
            {t('projects.editor.fileTree')}
          </Text>
          <DirectoryTree
            treeData={treeData}
            loadData={onLoadData}
            onSelect={onSelect}
            expandedKeys={expandedKeys}
            onExpand={(keys) => setExpandedKeys(keys)}
            showIcon
          />
        </div>
      </Sider>
      
      <Content className="flex flex-col bg-white">
        {/* Editor Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-50">
          <div>
            {currentPath ? (
              <Breadcrumb
                items={currentPath.split('/').map((part, index, arr) => ({
                  title: part,
                }))}
              />
            ) : (
              <Text type="secondary">{t('projects.editor.noFileSelected')}</Text>
            )}
          </div>
          <Space>
            {project?.git_url && (
              <>
                <Tooltip title={t('projects.gitPull')}>
                  <Button icon={<CloudDownloadOutlined />} onClick={handlePull} />
                </Tooltip>
                <Tooltip title={t('projects.gitPush')}>
                  <Button icon={<CloudUploadOutlined />} onClick={handlePush} />
                </Tooltip>
              </>
            )}
            <Button
              icon={<SaveOutlined />}
              onClick={() => handleSave(false)}
              disabled={!hasChanges}
              loading={saving}
            >
              {t('projects.editor.save')}
            </Button>
            {project?.git_url && (
              <Button
                type="primary"
                onClick={() => setCommitModalVisible(true)}
                disabled={!hasChanges}
              >
                {t('projects.editor.saveAndCommit')}
              </Button>
            )}
          </Space>
        </div>
        
        {/* Editor Content */}
        <div className="flex-1 overflow-hidden">
          {fileLoading ? (
            <div className="flex justify-center items-center h-full">
              <Spin />
            </div>
          ) : currentPath ? (
            <Editor
              height="100%"
              language={getLanguageFromPath(currentPath)}
              value={currentContent}
              onChange={handleEditorChange}
              onMount={(editor) => {
                editorRef.current = editor
              }}
              options={{
                minimap: { enabled: true },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
                scrollBeyondLastLine: false,
              }}
            />
          ) : (
            <Empty
              description={t('projects.editor.noFileSelected')}
              className="mt-20"
            />
          )}
        </div>
      </Content>

      {/* Commit Modal */}
      <Modal
        title={t('projects.editor.saveAndCommit')}
        open={commitModalVisible}
        onCancel={() => setCommitModalVisible(false)}
        onOk={() => handleSave(true)}
        confirmLoading={saving}
      >
        <Input.TextArea
          placeholder={t('projects.editor.enterCommitMessage')}
          value={commitMessage}
          onChange={(e) => setCommitMessage(e.target.value)}
          rows={3}
        />
      </Modal>
    </Layout>
  )
}

export default ProjectEditor
