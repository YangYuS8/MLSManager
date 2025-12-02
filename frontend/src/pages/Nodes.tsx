import { useRef, useState } from 'react'
import {
  ProTable,
  ProColumns,
  ActionType,
  ModalForm,
  ProFormText,
  ProFormSelect,
  ProFormDigit,
} from '@ant-design/pro-components'
import { Tag, Button, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listNodesApiV1NodesGet,
  registerNodeApiV1NodesPost,
  deleteNodeApiV1NodesNodeIdDelete,
  getNodeStatsApiV1NodesStatsGet,
  type NodeRead,
  type NodeCreate,
  type NodeStats,
} from '../api/client'

const statusColorMap: Record<string, string> = {
  online: 'success',
  offline: 'default',
  maintenance: 'warning',
}

const Nodes: React.FC = () => {
  const actionRef = useRef<ActionType>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [stats, setStats] = useState<NodeStats | null>(null)
  const { t } = useTranslation()

  const fetchStats = async () => {
    const { data } = await getNodeStatsApiV1NodesStatsGet()
    if (data) setStats(data)
  }

  const handleCreate = async (values: NodeCreate) => {
    try {
      const { error } = await registerNodeApiV1NodesPost({ body: values })
      if (error) {
        message.error(t('nodes.createFailed'))
        return false
      }
      message.success(t('nodes.createSuccess'))
      actionRef.current?.reload()
      return true
    } catch (err) {
      message.error(t('nodes.createFailed'))
      return false
    }
  }

  const handleDelete = async (nodeId: string) => {
    try {
      const { error } = await deleteNodeApiV1NodesNodeIdDelete({
        path: { node_id: nodeId },
      })
      if (error) {
        message.error(t('nodes.deleteFailed'))
        return
      }
      message.success(t('nodes.deleteSuccess'))
      actionRef.current?.reload()
    } catch (err) {
      message.error(t('nodes.deleteFailed'))
    }
  }

  const columns: ProColumns<NodeRead>[] = [
    {
      title: t('nodes.nodeId'),
      dataIndex: 'node_id',
      copyable: true,
      width: 150,
    },
    {
      title: t('common.name'),
      dataIndex: 'name',
    },
    {
      title: t('nodes.nodeType'),
      dataIndex: 'node_type',
      valueEnum: {
        master: { text: t('nodes.master'), status: 'Success' },
        worker: { text: t('nodes.worker'), status: 'Processing' },
      },
      width: 100,
    },
    {
      title: t('nodes.host'),
      render: (_, record) => `${record.host}:${record.port}`,
      width: 180,
    },
    {
      title: t('common.status'),
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>
          {record.status === 'online' ? t('nodes.online') : t('nodes.offline')}
        </Tag>
      ),
      width: 100,
    },
    {
      title: 'Resources',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          {record.cpu_count && <span>CPU: {record.cpu_count} cores</span>}
          {record.memory_total_gb && <span>RAM: {record.memory_total_gb} GB</span>}
          {record.gpu_count !== null && record.gpu_count !== undefined && (
            <span>GPU: {record.gpu_count}</span>
          )}
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
      title: t('nodes.lastHeartbeat'),
      dataIndex: 'last_heartbeat',
      valueType: 'dateTime',
      width: 160,
    },
    {
      title: t('common.actions'),
      valueType: 'option',
      width: 100,
      render: (_, record) => (
        <Popconfirm
          title={t('nodes.deleteConfirm')}
          onConfirm={() => handleDelete(record.node_id)}
          okText={t('common.yes')}
          cancelText={t('common.no')}
        >
          <Button size="small" danger icon={<DeleteOutlined />}>
            {t('common.delete')}
          </Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <ProTable<NodeRead>
        headerTitle={
          <Space>
            <span>{t('nodes.title')}</span>
            {stats && (
              <Tag color="blue">
                {stats.online_nodes}/{stats.total_nodes} {t('nodes.online').toLowerCase()}
              </Tag>
            )}
          </Space>
        }
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async () => {
          const { data, error } = await listNodesApiV1NodesGet()
          if (error) {
            return { data: [], success: false, total: 0 }
          }
          fetchStats()
          return {
            data: data || [],
            success: true,
            total: data?.length || 0,
          }
        }}
        toolBarRender={() => [
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => actionRef.current?.reload()}
          >
            {t('common.reset')}
          </Button>,
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
          >
            {t('nodes.createNode')}
          </Button>,
        ]}
        pagination={{
          pageSize: 10,
        }}
      />

      <ModalForm<NodeCreate>
        title={t('nodes.createNode')}
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={handleCreate}
        modalProps={{ destroyOnClose: true }}
        width={500}
      >
        <ProFormText
          name="node_id"
          label={t('nodes.nodeId')}
          placeholder="e.g., worker-01"
          rules={[{ required: true }]}
        />
        <ProFormText
          name="name"
          label={t('nodes.nodeName')}
          placeholder="e.g., GPU Server 1"
          rules={[{ required: true }]}
        />
        <ProFormSelect
          name="node_type"
          label={t('nodes.nodeType')}
          initialValue="worker"
          options={[
            { label: t('nodes.worker'), value: 'worker' },
            { label: t('nodes.master'), value: 'master' },
          ]}
          rules={[{ required: true }]}
        />
        <ProFormText
          name="host"
          label={t('nodes.host')}
          placeholder="e.g., 192.168.1.100"
          rules={[{ required: true }]}
        />
        <ProFormDigit
          name="port"
          label={t('nodes.port')}
          initialValue={8080}
          min={1}
          max={65535}
          rules={[{ required: true }]}
        />
        <ProFormText
          name="storage_path"
          label={t('datasets.datasetPath')}
          placeholder="e.g., /data"
        />
      </ModalForm>
    </>
  )
}

export default Nodes
