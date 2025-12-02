import { useRef, useState } from 'react'
import {
  ProTable,
  ProColumns,
  ActionType,
  ModalForm,
  ProFormText,
  ProFormTextArea,
  ProFormSelect,
} from '@ant-design/pro-components'
import { Tag, Button, message, Popconfirm, Input } from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  DeleteOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listDatasetsApiV1DatasetsGet,
  createDatasetApiV1DatasetsPost,
  deleteDatasetApiV1DatasetsDatasetIdDelete,
  searchDatasetsApiV1DatasetsSearchGet,
  listNodesApiV1NodesGet,
  type DatasetRead,
  type DatasetCreate,
  type NodeRead,
} from '../api/client'

const statusColorMap: Record<string, string> = {
  available: 'success',
  pending: 'default',
  syncing: 'processing',
  error: 'error',
}

const formatBytes = (bytes: number | null | undefined): string => {
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
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [nodes, setNodes] = useState<NodeRead[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const { t } = useTranslation()

  const fetchNodes = async () => {
    const { data } = await listNodesApiV1NodesGet()
    setNodes(data || [])
  }

  const handleCreate = async (values: DatasetCreate) => {
    try {
      const { error } = await createDatasetApiV1DatasetsPost({ body: values })
      if (error) {
        message.error(t('datasets.createFailed'))
        return false
      }
      message.success(t('datasets.createSuccess'))
      actionRef.current?.reload()
      return true
    } catch (err) {
      message.error(t('datasets.createFailed'))
      return false
    }
  }

  const handleDelete = async (datasetId: number) => {
    try {
      const { error } = await deleteDatasetApiV1DatasetsDatasetIdDelete({
        path: { dataset_id: datasetId },
      })
      if (error) {
        message.error(t('datasets.deleteFailed'))
        return
      }
      message.success(t('datasets.deleteSuccess'))
      actionRef.current?.reload()
    } catch (err) {
      message.error(t('datasets.deleteFailed'))
    }
  }

  const handleSearch = async () => {
    actionRef.current?.reload()
  }

  const columns: ProColumns<DatasetRead>[] = [
    {
      title: t('common.name'),
      dataIndex: 'name',
      copyable: true,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      width: 100,
    },
    {
      title: t('datasets.format'),
      dataIndex: 'format',
      render: (text) => text || '-',
      width: 100,
    },
    {
      title: t('datasets.datasetPath'),
      dataIndex: 'local_path',
      ellipsis: true,
      width: 200,
    },
    {
      title: t('datasets.size'),
      dataIndex: 'size_bytes',
      render: (_, record) => formatBytes(record.size_bytes),
      width: 100,
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      render: (text) => text ?? '-',
      width: 80,
    },
    {
      title: t('datasets.nodeId'),
      dataIndex: 'node_id',
      width: 80,
    },
    {
      title: t('common.status'),
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>
          {record.status === 'available' ? t('datasets.available') : record.status}
        </Tag>
      ),
      width: 100,
    },
    {
      title: t('common.createdAt'),
      dataIndex: 'created_at',
      valueType: 'dateTime',
      width: 160,
    },
    {
      title: t('common.actions'),
      valueType: 'option',
      width: 100,
      render: (_, record) => (
        <Popconfirm
          title={t('datasets.deleteConfirm')}
          onConfirm={() => handleDelete(record.id)}
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
      <ProTable<DatasetRead>
        headerTitle={t('datasets.title')}
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async () => {
          let response
          if (searchQuery.trim()) {
            response = await searchDatasetsApiV1DatasetsSearchGet({
              query: { q: searchQuery },
            })
          } else {
            response = await listDatasetsApiV1DatasetsGet()
          }
          const { data, error } = response
          if (error) {
            return { data: [], success: false, total: 0 }
          }
          return {
            data: data || [],
            success: true,
            total: data?.length || 0,
          }
        }}
        toolBarRender={() => [
          <Input.Search
            key="search"
            placeholder={t('datasets.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 250 }}
            enterButton={<SearchOutlined />}
            allowClear
          />,
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => {
              setSearchQuery('')
              actionRef.current?.reload()
            }}
          >
            {t('common.reset')}
          </Button>,
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              fetchNodes()
              setCreateModalOpen(true)
            }}
          >
            {t('datasets.createDataset')}
          </Button>,
        ]}
        pagination={{
          pageSize: 10,
        }}
      />

      <ModalForm<DatasetCreate>
        title={t('datasets.createDataset')}
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={handleCreate}
        modalProps={{ destroyOnClose: true }}
        width={500}
      >
        <ProFormText
          name="name"
          label={t('datasets.datasetName')}
          placeholder="e.g., ImageNet-2012"
          rules={[{ required: true }]}
        />
        <ProFormTextArea
          name="description"
          label={t('common.description')}
          placeholder={t('common.description')}
        />
        <ProFormText
          name="version"
          label="Version"
          initialValue="1.0.0"
          placeholder="e.g., 1.0.0"
        />
        <ProFormSelect
          name="node_id"
          label={t('datasets.nodeId')}
          options={nodes.map((n) => ({
            label: `${n.name} (${n.node_id})`,
            value: n.id,
          }))}
          rules={[{ required: true }]}
        />
        <ProFormText
          name="local_path"
          label={t('datasets.datasetPath')}
          placeholder="e.g., /data/datasets/imagenet"
          rules={[{ required: true }]}
        />
        <ProFormSelect
          name="format"
          label={t('datasets.format')}
          options={[
            { label: 'Images', value: 'images' },
            { label: 'CSV', value: 'csv' },
            { label: 'Parquet', value: 'parquet' },
            { label: 'JSON', value: 'json' },
            { label: 'HDF5', value: 'hdf5' },
            { label: 'Other', value: 'other' },
          ]}
        />
      </ModalForm>
    </>
  )
}

export default Datasets
