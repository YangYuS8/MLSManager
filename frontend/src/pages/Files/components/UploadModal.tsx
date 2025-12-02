import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Upload, message, Progress, List, Space } from 'antd'
import { InboxOutlined, FileOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps, RcFile } from 'antd/es/upload'
import { getToken } from '../../../utils/auth'

const { Dragger } = Upload

interface UploadModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  currentPath: string
}

interface UploadStatus {
  file: string
  status: 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

const UploadModal: React.FC<UploadModalProps> = ({
  open,
  onClose,
  onSuccess,
  currentPath,
}) => {
  const { t } = useTranslation()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([])

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning(t('files.selectFiles'))
      return
    }

    setUploading(true)
    const statuses: UploadStatus[] = fileList.map((f) => ({
      file: f.name,
      status: 'uploading' as const,
      progress: 0,
    }))
    setUploadStatuses(statuses)

    let successCount = 0
    let errorCount = 0

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      try {
        const formData = new FormData()
        // originFileObj contains the actual File object when using beforeUpload
        // If it's a RcFile added directly, use it as is
        const fileBlob = file.originFileObj || (file as unknown as RcFile)
        if (!fileBlob) {
          throw new Error('No file data available')
        }
        formData.append('file', fileBlob, file.name)

        const token = getToken()
        const response = await fetch(
          `/api/v1/files/upload?path=${encodeURIComponent(currentPath)}&overwrite=false`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          }
        )

        if (response.ok) {
          statuses[i] = { file: file.name, status: 'success', progress: 100 }
          successCount++
        } else {
          const error = await response.json()
          // Handle FastAPI validation errors (422) which return {detail: [{msg: string}]}
          let errorMessage = t('files.uploadFailed')
          if (error.detail) {
            if (typeof error.detail === 'string') {
              errorMessage = error.detail
            } else if (Array.isArray(error.detail) && error.detail.length > 0) {
              errorMessage = error.detail.map((e: { msg?: string }) => e.msg || '').join(', ')
            }
          }
          statuses[i] = {
            file: file.name,
            status: 'error',
            progress: 0,
            error: errorMessage,
          }
          errorCount++
        }
      } catch {
        statuses[i] = {
          file: file.name,
          status: 'error',
          progress: 0,
          error: t('files.uploadFailed'),
        }
        errorCount++
      }
      setUploadStatuses([...statuses])
    }

    setUploading(false)

    if (successCount > 0) {
      message.success(t('files.uploadSuccess', { count: successCount }))
    }
    if (errorCount > 0) {
      message.error(t('files.uploadErrors', { count: errorCount }))
    }

    if (successCount > 0) {
      setFileList([])
      setUploadStatuses([])
      onSuccess()
    }
  }

  const uploadProps: UploadProps = {
    multiple: true,
    fileList,
    beforeUpload: (file: RcFile) => {
      // Store the RcFile with originFileObj properly set
      const uploadFile: UploadFile = {
        uid: file.uid,
        name: file.name,
        size: file.size,
        type: file.type,
        originFileObj: file,
      }
      setFileList((prev) => [...prev, uploadFile])
      return false // Prevent auto upload
    },
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f.uid !== file.uid))
    },
  }

  const handleClose = () => {
    setFileList([])
    setUploadStatuses([])
    onClose()
  }

  return (
    <Modal
      title={t('files.upload')}
      open={open}
      onOk={handleUpload}
      onCancel={handleClose}
      okText={t('files.startUpload')}
      cancelText={t('common.cancel')}
      confirmLoading={uploading}
      width={600}
      destroyOnClose
    >
      <Dragger {...uploadProps} disabled={uploading}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{t('files.dropFiles')}</p>
        <p className="ant-upload-hint">{t('files.uploadHint')}</p>
      </Dragger>

      {uploadStatuses.length > 0 && (
        <List
          className="mt-4"
          size="small"
          dataSource={uploadStatuses}
          renderItem={(item) => (
            <List.Item>
              <Space className="w-full justify-between">
                <Space>
                  <FileOutlined />
                  <span>{item.file}</span>
                </Space>
                {item.status === 'uploading' && (
                  <Progress percent={item.progress} size="small" style={{ width: 100 }} />
                )}
                {item.status === 'success' && (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                )}
                {item.status === 'error' && (
                  <Space>
                    <span className="text-red-500 text-xs">{item.error}</span>
                    <CloseCircleOutlined style={{ color: '#f5222d' }} />
                  </Space>
                )}
              </Space>
            </List.Item>
          )}
        />
      )}
    </Modal>
  )
}

export default UploadModal
