import { useRef } from 'react'
import { ProTable, ProColumns, ActionType } from '@ant-design/pro-components'
import { Tag, Button } from 'antd'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../utils/api'

interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

const roleColorMap: Record<string, string> = {
  superadmin: 'red',
  admin: 'orange',
  member: 'blue',
}

const Users: React.FC = () => {
  const actionRef = useRef<ActionType>()

  const columns: ProColumns<User>[] = [
    {
      title: 'Username',
      dataIndex: 'username',
      copyable: true,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      copyable: true,
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      render: (text) => text || '-',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      render: (_, record) => (
        <Tag color={roleColorMap[record.role] || 'default'}>{record.role.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      render: (_, record) => (
        <Tag color={record.is_active ? 'success' : 'default'}>
          {record.is_active ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      valueType: 'dateTime',
    },
  ]

  return (
    <ProTable<User>
      headerTitle="Users"
      actionRef={actionRef}
      rowKey="id"
      columns={columns}
      request={async () => {
        try {
          const response = await api.get('/users/')
          return {
            data: response.data,
            success: true,
            total: response.data.length,
          }
        } catch (error) {
          return {
            data: [],
            success: false,
            total: 0,
          }
        }
      }}
      toolBarRender={() => [
        <Button key="refresh" icon={<ReloadOutlined />} onClick={() => actionRef.current?.reload()}>
          Refresh
        </Button>,
        <Button key="add" type="primary" icon={<PlusOutlined />}>
          Add User
        </Button>,
      ]}
      pagination={{
        pageSize: 10,
      }}
    />
  )
}

export default Users
