import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Drawer, Spin, Button, Space, message, Descriptions, Image } from 'antd'
import {
  EditOutlined,
  SaveOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import {
  readFileApiV1FilesReadGet,
  writeFileApiV1FilesWritePut,
  type FileInfo,
} from '../../../api/client'

interface FilePreviewProps {
  file: FileInfo | null
  onClose: () => void
  onRefresh: () => void
}

const FilePreview: React.FC<FilePreviewProps> = ({ file, onClose, onRefresh }) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [content, setContent] = useState('')
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  const isTextFile = (file: FileInfo | null): boolean => {
    if (!file) return false
    const textExtensions = [
      'txt', 'md', 'mdx', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf',
      'log', 'csv', 'js', 'ts', 'jsx', 'tsx', 'py', 'java', 'c', 'cpp', 'h', 'hpp',
      'go', 'rs', 'rb', 'php', 'sh', 'bash', 'zsh', 'fish', 'css', 'scss', 'less',
      'html', 'htm', 'vue', 'svelte', 'sql', 'graphql', 'dockerfile', 'makefile',
      'gitignore', 'env', 'editorconfig', 'prettierrc', 'eslintrc',
    ]
    const ext = file.extension?.toLowerCase() || ''
    const name = file.name.toLowerCase()
    return (
      textExtensions.includes(ext) ||
      name === 'dockerfile' ||
      name === 'makefile' ||
      name.startsWith('.')
    )
  }

  const isImageFile = (file: FileInfo | null): boolean => {
    if (!file) return false
    const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico']
    return imageExtensions.includes(file.extension?.toLowerCase() || '')
  }

  useEffect(() => {
    if (file && isTextFile(file)) {
      loadFileContent()
    } else {
      setContent('')
    }
    setEditing(false)
    setEditContent('')
  }, [file])

  const loadFileContent = async () => {
    if (!file) return
    setLoading(true)
    try {
      const { data, error } = await readFileApiV1FilesReadGet({
        query: {
          path: file.path,
          encoding: 'utf-8',
          max_size: 5 * 1024 * 1024, // 5MB
        },
      })
      if (error) {
        message.error(t('files.readFailed'))
        return
      }
      setContent(data?.content || '')
    } catch {
      message.error(t('files.readFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = () => {
    setEditContent(content)
    setEditing(true)
  }

  const handleSave = async () => {
    if (!file) return
    setSaving(true)
    try {
      const { error } = await writeFileApiV1FilesWritePut({
        body: {
          path: file.path,
          content: editContent,
          encoding: 'utf-8',
        },
      })
      if (error) {
        message.error(t('files.saveFailed'))
        return
      }
      message.success(t('files.saveSuccess'))
      setContent(editContent)
      setEditing(false)
      onRefresh()
    } catch {
      message.error(t('files.saveFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setEditing(false)
    setEditContent('')
  }

  const formatSize = (size: number) => {
    const units = ['B', 'KB', 'MB', 'GB']
    let unitIndex = 0
    let displaySize = size
    while (displaySize >= 1024 && unitIndex < units.length - 1) {
      displaySize /= 1024
      unitIndex++
    }
    return `${displaySize.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
  }

  return (
    <Drawer
      title={file?.name || t('files.preview')}
      open={!!file}
      onClose={onClose}
      width={800}
      extra={
        <Space>
          {isTextFile(file) && !editing && (
            <Button icon={<EditOutlined />} onClick={handleEdit}>
              {t('common.edit')}
            </Button>
          )}
          {editing && (
            <>
              <Button onClick={handleCancelEdit}>{t('common.cancel')}</Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={saving}
              >
                {t('common.save')}
              </Button>
            </>
          )}
        </Space>
      }
    >
      {file && (
        <>
          {/* File info */}
          <Descriptions size="small" column={2} className="mb-4">
            <Descriptions.Item label={t('files.path')}>{file.path}</Descriptions.Item>
            <Descriptions.Item label={t('files.size')}>
              {formatSize(file.size ?? 0)}
            </Descriptions.Item>
            <Descriptions.Item label={t('files.permissions')}>
              {file.mode} ({file.mode_octal})
            </Descriptions.Item>
            <Descriptions.Item label={t('files.owner')}>
              {file.owner}:{file.group}
            </Descriptions.Item>
            <Descriptions.Item label={t('files.modified')}>
              {new Date(file.modified_at).toLocaleString()}
            </Descriptions.Item>
            {file.mime_type && (
              <Descriptions.Item label={t('files.mimeType')}>
                {file.mime_type}
              </Descriptions.Item>
            )}
          </Descriptions>

          {/* Content preview */}
          {loading ? (
            <div className="flex justify-center py-8">
              <Spin size="large" />
            </div>
          ) : isTextFile(file) ? (
            editing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-96 p-2 font-mono text-sm border rounded focus:outline-none focus:border-blue-500"
                style={{ resize: 'vertical' }}
              />
            ) : (
              <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96 text-sm">
                <code>{content || t('files.emptyFile')}</code>
              </pre>
            )
          ) : isImageFile(file) ? (
            <div className="flex justify-center">
              <Image
                src={`/api/v1/files/download?path=${encodeURIComponent(file.path)}`}
                alt={file.name}
                style={{ maxHeight: 500 }}
              />
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>{t('files.cannotPreview')}</p>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                className="mt-4"
                href={`/api/v1/files/download?path=${encodeURIComponent(file.path)}`}
              >
                {t('files.download')}
              </Button>
            </div>
          )}
        </>
      )}
    </Drawer>
  )
}

export default FilePreview
