import { useRef } from 'react'
import { ProTable, ProColumns, ActionType } from '@ant-design/pro-components'
import { Tag, Button, Space } from 'antd'
import { PlusOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons'
import api from '../utils/api'

interface Job {
  id: number
  name: string
  description: string | null
  owner_id: number
  node_id: number | null
  job_type: string
  image: string | null
  command: string
  status: string
  exit_code: number | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

const statusColorMap: Record<string, string> = {
  pending: 'default',
  queued: 'processing',
  running: 'blue',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
}

const Jobs: React.FC = () => {
  const actionRef = useRef<ActionType>()

  const handleCancel = async (jobId: number) => {
    try {
      await api.post(`/jobs/${jobId}/cancel`)
      actionRef.current?.reload()
    } catch (error) {
      // Error handled by interceptor
    }
  }

  const columns: ProColumns<Job>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      copyable: true,
    },
    {
      title: 'Type',
      dataIndex: 'job_type',
      valueEnum: {
        docker: { text: 'Docker', status: 'Processing' },
        conda: { text: 'Conda', status: 'Success' },
        venv: { text: 'Venv', status: 'Default' },
      },
    },
    {
      title: 'Command',
      dataIndex: 'command',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>{record.status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Exit Code',
      dataIndex: 'exit_code',
      render: (text) => text ?? '-',
      width: 100,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      valueType: 'dateTime',
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      valueType: 'dateTime',
    },
    {
      title: 'Actions',
      valueType: 'option',
      render: (_, record) => (
        <Space>
          {['pending', 'queued', 'running'].includes(record.status) && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancel(record.id)}
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <ProTable<Job>
      headerTitle="Jobs"
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async () => {
        const response = await api.get('/jobs/')
        return {
          data: response.data,
          success: true,
          total: response.data.length,
        }
      }}
      toolBarRender={() => [
        <Button key="refresh" icon={<ReloadOutlined />} onClick={() => actionRef.current?.reload()}>
          Refresh
        </Button>,
        <Button key="add" type="primary" icon={<PlusOutlined />}>
          Submit Job
        </Button>,
      ]}
      pagination={{
        pageSize: 10,
      }}
    />
  )
}

export default Jobs
