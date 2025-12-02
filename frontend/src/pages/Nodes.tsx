import { useRef } from 'react'
import { ProTable, ProColumns, ActionType } from '@ant-design/pro-components'
import { Tag, Button, Space } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../utils/api'

interface Node {
  id: number
  node_id: string
  name: string
  node_type: string
  host: string
  port: number
  status: string
  cpu_count: number | null
  memory_total_gb: number | null
  gpu_count: number | null
  storage_total_gb: number | null
  storage_used_gb: number | null
  last_heartbeat: string | null
}

const statusColorMap: Record<string, string> = {
  online: 'success',
  offline: 'default',
  maintenance: 'warning',
}

const Nodes: React.FC = () => {
  const actionRef = useRef<ActionType>()

  const columns: ProColumns<Node>[] = [
    {
      title: 'Node ID',
      dataIndex: 'node_id',
      copyable: true,
    },
    {
      title: 'Name',
      dataIndex: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'node_type',
      valueEnum: {
        master: { text: 'Master', status: 'Success' },
        worker: { text: 'Worker', status: 'Processing' },
      },
    },
    {
      title: 'Host',
      dataIndex: 'host',
      render: (_, record) => `${record.host}:${record.port}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>{record.status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Resources',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          {record.cpu_count && <span>CPU: {record.cpu_count} cores</span>}
          {record.memory_total_gb && <span>RAM: {record.memory_total_gb} GB</span>}
          {record.gpu_count !== null && <span>GPU: {record.gpu_count}</span>}
        </Space>
      ),
    },
    {
      title: 'Storage',
      render: (_, record) => {
        if (!record.storage_total_gb) return '-'
        const used = record.storage_used_gb || 0
        const total = record.storage_total_gb
        const percent = Math.round((used / total) * 100)
        return `${used}/${total} GB (${percent}%)`
      },
    },
    {
      title: 'Last Heartbeat',
      dataIndex: 'last_heartbeat',
      valueType: 'dateTime',
    },
  ]

  return (
    <ProTable<Node>
      headerTitle="Compute Nodes"
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async () => {
        const response = await api.get('/nodes/')
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
          Add Node
        </Button>,
      ]}
      pagination={{
        pageSize: 10,
      }}
    />
  )
}

export default Nodes
