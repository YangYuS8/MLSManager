import React, { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  message,
  Popconfirm,
  Tooltip,
  Modal,
  Form,
  Select,
  Switch,
  Typography,
  Badge,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  FolderOpenOutlined,
  DeleteOutlined,
  EditOutlined,
  SyncOutlined,
  CloudDownloadOutlined,
  CloudUploadOutlined,
  GithubOutlined,
  SearchOutlined,
  CodeOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { getToken } from '../../utils/auth'
import { useNodeContext } from '../../contexts/NodeContext'

const { Title, Text } = Typography
const { TextArea } = Input

interface Project {
  id: number
  name: string
  description: string | null
  git_url: string | null
  git_branch: string
  local_path: string
  status: 'active' | 'archived' | 'syncing' | 'error'
  last_sync_at: string | null
  sync_error: string | null
  node_id: number
  owner_id: number
  is_public: boolean
  auto_sync: boolean
  created_at: string
  updated_at: string
}

interface Node {
  id: number
  name: string
  node_id: string
}

const Projects: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { currentNode } = useNodeContext()
  const [projects, setProjects] = useState<Project[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [cloneModalVisible, setCloneModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [cloneForm] = Form.useForm()

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    try {
      const url = currentNode
        ? `/api/v1/projects?node_id=${currentNode.id}`
        : '/api/v1/projects'
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setProjects(data)
      }
    } catch (err) {
      console.error('Failed to fetch projects:', err)
    } finally {
      setLoading(false)
    }
  }, [currentNode])

  const fetchNodes = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/nodes', {
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setNodes(data)
      }
    } catch (err) {
      console.error('Failed to fetch nodes:', err)
    }
  }, [])

  useEffect(() => {
    fetchProjects()
    fetchNodes()
  }, [fetchProjects, fetchNodes])

  const handleCreate = async (values: Record<string, unknown>) => {
    try {
      const response = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(values),
      })

      if (response.ok) {
        message.success(t('projects.createSuccess'))
        setCreateModalVisible(false)
        form.resetFields()
        fetchProjects()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.createFailed'))
      }
    } catch (err) {
      message.error(t('projects.createFailed'))
    }
  }

  const handleClone = async (values: Record<string, unknown>) => {
    try {
      const response = await fetch('/api/v1/projects/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(values),
      })

      if (response.ok) {
        message.success(t('projects.cloneSuccess'))
        setCloneModalVisible(false)
        cloneForm.resetFields()
        fetchProjects()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.cloneFailed'))
      }
    } catch (err) {
      message.error(t('projects.cloneFailed'))
    }
  }

  const handleDelete = async (id: number, deleteFiles: boolean = false) => {
    try {
      const response = await fetch(`/api/v1/projects/${id}?delete_files=${deleteFiles}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })

      if (response.ok) {
        message.success(t('projects.deleteSuccess'))
        fetchProjects()
      } else {
        message.error(t('projects.deleteFailed'))
      }
    } catch (err) {
      message.error(t('projects.deleteFailed'))
    }
  }

  const handlePull = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/projects/${id}/git/pull`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })

      if (response.ok) {
        message.success(t('projects.pullSuccess'))
        fetchProjects()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.pullFailed'))
      }
    } catch (err) {
      message.error(t('projects.pullFailed'))
    }
  }

  const handlePush = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/projects/${id}/git/push`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })

      if (response.ok) {
        message.success(t('projects.pushSuccess'))
        fetchProjects()
      } else {
        const error = await response.json()
        message.error(error.detail || t('projects.pushFailed'))
      }
    } catch (err) {
      message.error(t('projects.pushFailed'))
    }
  }

  const getStatusTag = (status: string) => {
    const statusConfig: Record<string, { color: string; label: string }> = {
      active: { color: 'green', label: t('projects.status.active') },
      archived: { color: 'default', label: t('projects.status.archived') },
      syncing: { color: 'processing', label: t('projects.status.syncing') },
      error: { color: 'red', label: t('projects.status.error') },
    }
    const config = statusConfig[status] || statusConfig.active
    return <Tag color={config.color}>{config.label}</Tag>
  }

  const columns: ColumnsType<Project> = [
    {
      title: t('projects.name'),
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Project) => (
        <Space>
          <FolderOpenOutlined />
          <span className="font-medium">{name}</span>
          {record.is_public && <Tag color="blue">Public</Tag>}
        </Space>
      ),
    },
    {
      title: t('projects.gitBranch'),
      dataIndex: 'git_branch',
      key: 'git_branch',
      width: 120,
      render: (branch: string, record: Project) =>
        record.git_url ? (
          <Tag icon={<GithubOutlined />}>{branch}</Tag>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: t('projects.status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: t('projects.lastSync'),
      dataIndex: 'last_sync_at',
      key: 'last_sync_at',
      width: 180,
      render: (date: string | null) =>
        date ? new Date(date).toLocaleString() : <Text type="secondary">-</Text>,
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 200,
      render: (_: unknown, record: Project) => (
        <Space size="small">
          <Tooltip title={t('projects.openEditor')}>
            <Button
              type="primary"
              size="small"
              icon={<CodeOutlined />}
              onClick={() => navigate(`/projects/${record.id}/editor`)}
            />
          </Tooltip>
          {record.git_url && (
            <>
              <Tooltip title={t('projects.gitPull')}>
                <Button
                  size="small"
                  icon={<CloudDownloadOutlined />}
                  onClick={() => handlePull(record.id)}
                  disabled={record.status === 'syncing'}
                />
              </Tooltip>
              <Tooltip title={t('projects.gitPush')}>
                <Button
                  size="small"
                  icon={<CloudUploadOutlined />}
                  onClick={() => handlePush(record.id)}
                  disabled={record.status === 'syncing'}
                />
              </Tooltip>
            </>
          )}
          <Popconfirm
            title={t('projects.deleteConfirm')}
            onConfirm={() => handleDelete(record.id, false)}
            okText={t('common.yes')}
            cancelText={t('common.no')}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchText.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchText.toLowerCase()))
  )

  return (
    <div>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <Title level={4} className="m-0">
            <FolderOpenOutlined className="mr-2" />
            {t('projects.title')}
          </Title>
          <Space>
            <Input
              placeholder={t('projects.searchPlaceholder')}
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button icon={<SyncOutlined />} onClick={fetchProjects}>
              {t('common.reset')}
            </Button>
            <Button icon={<GithubOutlined />} onClick={() => setCloneModalVisible(true)}>
              {t('projects.cloneProject')}
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              {t('projects.createProject')}
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={filteredProjects}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `${t('files.totalItems', { count: total })}`,
          }}
        />
      </Card>

      {/* Create Project Modal */}
      <Modal
        title={t('projects.createProject')}
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label={t('projects.name')}
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label={t('projects.description')}>
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item
            name="local_path"
            label={t('projects.localPath')}
            rules={[{ required: true }]}
          >
            <Input placeholder="/data/projects/my-project" />
          </Form.Item>
          <Form.Item
            name="node_id"
            label={t('projects.node')}
            rules={[{ required: true }]}
            initialValue={currentNode?.id}
          >
            <Select>
              {nodes.map((node) => (
                <Select.Option key={node.id} value={node.id}>
                  {node.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="is_public" label={t('projects.isPublic')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {t('common.create')}
              </Button>
              <Button onClick={() => setCreateModalVisible(false)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Clone Project Modal */}
      <Modal
        title={t('projects.cloneProject')}
        open={cloneModalVisible}
        onCancel={() => setCloneModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={cloneForm} layout="vertical" onFinish={handleClone}>
          <Form.Item
            name="git_url"
            label={t('projects.gitUrl')}
            rules={[{ required: true }, { type: 'url' }]}
          >
            <Input placeholder="https://github.com/user/repo.git" />
          </Form.Item>
          <Form.Item
            name="name"
            label={t('projects.name')}
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label={t('projects.description')}>
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item
            name="git_branch"
            label={t('projects.gitBranch')}
            initialValue="main"
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="node_id"
            label={t('projects.node')}
            rules={[{ required: true }]}
            initialValue={currentNode?.id}
          >
            <Select>
              {nodes.map((node) => (
                <Select.Option key={node.id} value={node.id}>
                  {node.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {t('projects.cloneProject')}
              </Button>
              <Button onClick={() => setCloneModalVisible(false)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Projects
