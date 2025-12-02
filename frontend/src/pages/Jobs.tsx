import { useRef, useState } from 'react'
import {
  ProTable,
  ProColumns,
  ActionType,
  ModalForm,
  ProFormText,
  ProFormTextArea,
  ProFormSelect,
  ProFormDigit,
} from '@ant-design/pro-components'
import { Tag, Button, Space, Modal, message } from 'antd'
import {
  PlusOutlined,
  ReloadOutlined,
  StopOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listJobsApiV1JobsGet,
  createJobApiV1JobsPost,
  cancelJobApiV1JobsJobIdCancelPost,
  getJobLogsApiV1JobsJobIdLogsGet,
  listNodesApiV1NodesGet,
  type JobRead,
  type JobCreate,
  type NodeRead,
} from '../api/client'

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
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [logModalOpen, setLogModalOpen] = useState(false)
  const [currentJobId, setCurrentJobId] = useState<number | null>(null)
  const [logContent, setLogContent] = useState<string>('')
  const [logLoading, setLogLoading] = useState(false)
  const [nodes, setNodes] = useState<NodeRead[]>([])
  const { t } = useTranslation()

  const handleCancel = async (jobId: number) => {
    try {
      const { error } = await cancelJobApiV1JobsJobIdCancelPost({
        path: { job_id: jobId },
      })
      if (error) {
        message.error(t('jobs.cancelFailed'))
        return
      }
      message.success(t('jobs.cancelSuccess'))
      actionRef.current?.reload()
    } catch (err) {
      message.error(t('jobs.cancelFailed'))
    }
  }

  const handleViewLogs = async (jobId: number) => {
    setCurrentJobId(jobId)
    setLogModalOpen(true)
    setLogLoading(true)
    try {
      const { data, error } = await getJobLogsApiV1JobsJobIdLogsGet({
        path: { job_id: jobId },
      })
      if (error || !data) {
        setLogContent(t('jobs.noLogs'))
      } else {
        setLogContent(data as string)
      }
    } catch (err) {
      setLogContent(t('jobs.noLogs'))
    } finally {
      setLogLoading(false)
    }
  }

  const handleCreateJob = async (values: JobCreate) => {
    try {
      const { error } = await createJobApiV1JobsPost({
        body: values,
      })
      if (error) {
        message.error(t('jobs.submitFailed'))
        return false
      }
      message.success(t('jobs.submitSuccess'))
      actionRef.current?.reload()
      return true
    } catch (err) {
      message.error(t('jobs.submitFailed'))
      return false
    }
  }

  const fetchNodes = async () => {
    const { data } = await listNodesApiV1NodesGet()
    setNodes(data || [])
  }

  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: t('jobs.status.pending'),
      queued: t('jobs.status.queued'),
      running: t('jobs.status.running'),
      completed: t('jobs.status.completed'),
      failed: t('jobs.status.failed'),
      cancelled: t('jobs.status.cancelled'),
    }
    return statusMap[status] || status
  }

  const columns: ProColumns<JobRead>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: t('common.name'),
      dataIndex: 'name',
      copyable: true,
    },
    {
      title: t('jobs.jobType'),
      dataIndex: 'job_type',
      valueEnum: {
        docker: { text: 'Docker', status: 'Processing' },
        conda: { text: 'Conda', status: 'Success' },
        venv: { text: 'Venv', status: 'Default' },
      },
      width: 100,
    },
    {
      title: t('jobs.command'),
      dataIndex: 'command',
      ellipsis: true,
      width: 200,
    },
    {
      title: t('common.status'),
      dataIndex: 'status',
      render: (_, record) => (
        <Tag color={statusColorMap[record.status] || 'default'}>
          {getStatusText(record.status)}
        </Tag>
      ),
      width: 100,
    },
    {
      title: t('jobs.targetNode'),
      dataIndex: 'node_id',
      render: (text) => text ?? '-',
      width: 100,
    },
    {
      title: 'Exit Code',
      dataIndex: 'exit_code',
      render: (text) => text ?? '-',
      width: 80,
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
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handleViewLogs(record.id)}
          >
            {t('jobs.viewLogs')}
          </Button>
          {['pending', 'queued', 'running'].includes(record.status) && (
            <Button
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancel(record.id)}
            >
              {t('jobs.cancelJob')}
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <>
      <ProTable<JobRead>
        headerTitle={t('jobs.title')}
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async () => {
          const { data, error } = await listJobsApiV1JobsGet()
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
            onClick={() => {
              fetchNodes()
              setCreateModalOpen(true)
            }}
          >
            {t('jobs.submitJob')}
          </Button>,
        ]}
        pagination={{
          pageSize: 10,
        }}
      />

      {/* Create Job Modal */}
      <ModalForm<JobCreate>
        title={t('jobs.submitJob')}
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={handleCreateJob}
        modalProps={{ destroyOnClose: true }}
        width={600}
      >
        <ProFormText
          name="name"
          label={t('jobs.jobName')}
          placeholder="Enter job name"
          rules={[{ required: true }]}
        />
        <ProFormTextArea
          name="description"
          label={t('common.description')}
          placeholder={t('common.description')}
        />
        <ProFormSelect
          name="job_type"
          label={t('jobs.jobType')}
          initialValue="docker"
          options={[
            { label: 'Docker', value: 'docker' },
            { label: 'Conda', value: 'conda' },
            { label: 'Venv', value: 'venv' },
          ]}
          rules={[{ required: true }]}
        />
        <ProFormText
          name="image"
          label="Docker Image"
          placeholder="e.g., pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime"
        />
        <ProFormText
          name="command"
          label={t('jobs.command')}
          placeholder="e.g., python train.py --epochs 100"
          rules={[{ required: true }]}
        />
        <ProFormText
          name="working_dir"
          label={t('jobs.workingDir')}
          placeholder="e.g., /workspace"
        />
        <ProFormSelect
          name="node_id"
          label={t('jobs.targetNode')}
          placeholder="-"
          options={nodes.map((n) => ({
            label: `${n.name} (${n.status})`,
            value: n.id,
          }))}
        />
        <Space style={{ width: '100%' }}>
          <ProFormDigit
            name="gpu_count"
            label="GPU"
            placeholder="0"
            min={0}
            max={8}
            width="sm"
          />
          <ProFormDigit
            name="memory_limit_gb"
            label="RAM (GB)"
            placeholder="Auto"
            min={1}
            max={512}
            width="sm"
          />
          <ProFormDigit
            name="cpu_limit"
            label="CPU"
            placeholder="Auto"
            min={1}
            max={128}
            width="sm"
          />
        </Space>
      </ModalForm>

      {/* Log Viewer Modal */}
      <Modal
        title={`${t('jobs.logs')} - #${currentJobId}`}
        open={logModalOpen}
        onCancel={() => setLogModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setLogModalOpen(false)}>
            {t('common.cancel')}
          </Button>,
          <Button
            key="refresh"
            type="primary"
            icon={<ReloadOutlined />}
            loading={logLoading}
            onClick={() => currentJobId && handleViewLogs(currentJobId)}
          >
            {t('common.reset')}
          </Button>,
        ]}
        width={800}
      >
        <pre
          style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: 16,
            borderRadius: 8,
            maxHeight: 500,
            overflow: 'auto',
            fontSize: 12,
            fontFamily: 'monospace',
          }}
        >
          {logLoading ? t('common.loading') : logContent || t('jobs.noLogs')}
        </pre>
      </Modal>
    </>
  )
}

export default Jobs
