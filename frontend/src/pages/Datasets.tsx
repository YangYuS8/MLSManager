import { useRef } from 'react'
import { ProTable, ProColumns, ActionType } from '@ant-design/pro-components'
import { Tag, Button } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../utils/api'

interface Dataset {
  id: number
  name: string
  description: string | null
  version: string
  node_id: number
  local_path: string
  size_bytes: number | null
  file_count: number | null
  format: string | null
  status: string
  created_at: string
}

const statusColorMap: Record<string, string> = {
  available: 'success',
  pending: 'default',
  syncing: 'processing',
  error: 'error',
}

const formatBytes = (bytes: number | null): string => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

const Datasets: React.FC = () => {
  const actionRef = useRef<ActionType>()

  const columns: ProColumns<Dataset>[] = [
    {
      title: 'Name',
      dataIndex: 'name',
      copyable: true,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      width: 100,
    },
    {
      title: 'Format',
      dataIndex: 'format',
      render: (text) => text || '-',
    },
    {
      title: 'Path',
      dataIndex: 'local_path',
      ellipsis: true,
    },
    {
      title: 'Size',
      dataIndex: 'size_bytes',
      render: (_, record) => formatBytes(record.size_bytes),
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      render: (text) => text ?? '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>{record.status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      valueType: 'dateTime',
    },
  ]

  return (
    <ProTable<Dataset>
      headerTitle="Datasets"
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async () => {
        const response = await api.get('/datasets/')
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
          Add Dataset
        </Button>,
      ]}
      pagination={{
        pageSize: 10,
      }}
    />
  )
}

export default Datasets
