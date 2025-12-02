import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Card,
  Button,
  Space,
  Input,
  Switch,
  Dropdown,
  message,
  Modal,
  Breadcrumb,
  Tooltip,
} from 'antd'
import {
  FolderOutlined,
  HomeOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  ReloadOutlined,
  UploadOutlined,
  FolderAddOutlined,
  FileAddOutlined,
  DeleteOutlined,
  SearchOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  DownloadOutlined,
  CopyOutlined,
  ScissorOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import FileTable from './components/FileTable'
import CreateModal from './components/CreateModal'
import UploadModal from './components/UploadModal'
import FilePreview from './components/FilePreview'
import MoveModal from './components/MoveModal'
import {
  listDirectoryApiV1FilesListGet,
  deleteFilesApiV1FilesDeleteDelete,
  type FileInfo,
} from '../../api/client'

const Files: React.FC = () => {
  const { t } = useTranslation()
  const [currentPath, setCurrentPath] = useState('/')
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [showHidden, setShowHidden] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [history, setHistory] = useState<string[]>(['/'])
  const [historyIndex, setHistoryIndex] = useState(0)
  const [selectedFiles, setSelectedFiles] = useState<FileInfo[]>([])

  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createIsDirectory, setCreateIsDirectory] = useState(false)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [previewFile, setPreviewFile] = useState<FileInfo | null>(null)
  const [moveModalOpen, setMoveModalOpen] = useState(false)
  const [moveMode, setMoveMode] = useState<'move' | 'copy'>('move')

  const fetchFiles = useCallback(async () => {
    setLoading(true)
    try {
      const { data, error } = await listDirectoryApiV1FilesListGet({
        query: {
          path: currentPath,
          show_hidden: showHidden,
          sort_by: 'name',
          sort_order: 'asc',
        },
      })
      if (error) {
        message.error(t('files.loadFailed'))
        return
      }
      setFiles(data?.items || [])
    } catch {
      message.error(t('files.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [currentPath, showHidden, t])

  useEffect(() => {
    fetchFiles()
  }, [fetchFiles])

  const navigateTo = (path: string) => {
    const newHistory = history.slice(0, historyIndex + 1)
    newHistory.push(path)
    setHistory(newHistory)
    setHistoryIndex(newHistory.length - 1)
    setCurrentPath(path)
    setSelectedFiles([])
  }

  const goBack = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1)
      setCurrentPath(history[historyIndex - 1])
      setSelectedFiles([])
    }
  }

  const goForward = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1)
      setCurrentPath(history[historyIndex + 1])
      setSelectedFiles([])
    }
  }

  const goUp = () => {
    if (currentPath !== '/') {
      const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/'
      navigateTo(parentPath)
    }
  }

  const handleFileClick = (file: FileInfo) => {
    if (file.type === 'directory') {
      navigateTo(file.path)
    } else {
      // Preview file
      setPreviewFile(file)
    }
  }

  const handleDelete = async () => {
    if (selectedFiles.length === 0) return

    Modal.confirm({
      title: t('files.confirmDelete'),
      content: t('files.deleteWarning', { count: selectedFiles.length }),
      okText: t('common.delete'),
      okType: 'danger',
      cancelText: t('common.cancel'),
      onOk: async () => {
        try {
          const { error } = await deleteFilesApiV1FilesDeleteDelete({
            body: {
              paths: selectedFiles.map((f) => f.path),
              recursive: true,
            },
          })
          if (error) {
            message.error(t('files.deleteFailed'))
            return
          }
          message.success(t('files.deleteSuccess'))
          setSelectedFiles([])
          fetchFiles()
        } catch {
          message.error(t('files.deleteFailed'))
        }
      },
    })
  }

  const handleDownload = async () => {
    if (selectedFiles.length !== 1) return
    const file = selectedFiles[0]
    if (file.type === 'directory') {
      message.warning(t('files.cannotDownloadDirectory'))
      return
    }

    try {
      // Create a download link
      const url = `/api/v1/files/download?path=${encodeURIComponent(file.path)}`
      const link = document.createElement('a')
      link.href = url
      link.download = file.name
      link.click()
    } catch {
      message.error(t('files.downloadFailed'))
    }
  }

  const handleMove = (mode: 'move' | 'copy') => {
    if (selectedFiles.length === 0) return
    setMoveMode(mode)
    setMoveModalOpen(true)
  }

  // Build breadcrumb items
  const breadcrumbItems = [
    {
      key: '/',
      title: (
        <a onClick={() => navigateTo('/')}>
          <HomeOutlined />
        </a>
      ),
    },
    ...currentPath
      .split('/')
      .filter(Boolean)
      .map((segment, index, arr) => {
        const path = '/' + arr.slice(0, index + 1).join('/')
        return {
          key: path,
          title: <a onClick={() => navigateTo(path)}>{segment}</a>,
        }
      }),
  ]

  // Filter files by search text
  const filteredFiles = searchText
    ? files.filter((f) =>
        f.name.toLowerCase().includes(searchText.toLowerCase())
      )
    : files

  // Context menu for selected files
  const contextMenuItems: MenuProps['items'] = [
    {
      key: 'download',
      label: t('files.download'),
      icon: <DownloadOutlined />,
      disabled: selectedFiles.length !== 1 || selectedFiles[0]?.type === 'directory',
      onClick: handleDownload,
    },
    { type: 'divider' },
    {
      key: 'copy',
      label: t('files.copy'),
      icon: <CopyOutlined />,
      disabled: selectedFiles.length === 0,
      onClick: () => handleMove('copy'),
    },
    {
      key: 'move',
      label: t('files.move'),
      icon: <ScissorOutlined />,
      disabled: selectedFiles.length === 0,
      onClick: () => handleMove('move'),
    },
    { type: 'divider' },
    {
      key: 'delete',
      label: t('common.delete'),
      icon: <DeleteOutlined />,
      danger: true,
      disabled: selectedFiles.length === 0,
      onClick: handleDelete,
    },
  ]

  return (
    <Card
      title={
        <Space>
          <FolderOutlined />
          {t('files.title')}
        </Space>
      }
    >
      {/* Toolbar */}
      <Space wrap className="mb-4 w-full">
        {/* Navigation buttons */}
        <Button.Group>
          <Tooltip title={t('files.back')}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={goBack}
              disabled={historyIndex === 0}
            />
          </Tooltip>
          <Tooltip title={t('files.forward')}>
            <Button
              icon={<ArrowRightOutlined />}
              onClick={goForward}
              disabled={historyIndex >= history.length - 1}
            />
          </Tooltip>
          <Tooltip title={t('files.up')}>
            <Button
              icon={<HomeOutlined />}
              onClick={goUp}
              disabled={currentPath === '/'}
            />
          </Tooltip>
          <Tooltip title={t('common.refresh')}>
            <Button icon={<ReloadOutlined />} onClick={fetchFiles} />
          </Tooltip>
        </Button.Group>

        {/* Create buttons */}
        <Button
          icon={<FolderAddOutlined />}
          onClick={() => {
            setCreateIsDirectory(true)
            setCreateModalOpen(true)
          }}
        >
          {t('files.newFolder')}
        </Button>
        <Button
          icon={<FileAddOutlined />}
          onClick={() => {
            setCreateIsDirectory(false)
            setCreateModalOpen(true)
          }}
        >
          {t('files.newFile')}
        </Button>
        <Button
          icon={<UploadOutlined />}
          type="primary"
          onClick={() => setUploadModalOpen(true)}
        >
          {t('files.upload')}
        </Button>

        {/* Selection actions */}
        {selectedFiles.length > 0 && (
          <>
            <Dropdown menu={{ items: contextMenuItems }} trigger={['click']}>
              <Button>
                {t('common.actions')} ({selectedFiles.length})
              </Button>
            </Dropdown>
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={handleDelete}
            >
              {t('common.delete')}
            </Button>
          </>
        )}

        {/* Search and toggle */}
        <Input
          prefix={<SearchOutlined />}
          placeholder={t('files.search')}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 200 }}
          allowClear
        />
        <Tooltip title={t('files.showHidden')}>
          <Switch
            checked={showHidden}
            onChange={setShowHidden}
            checkedChildren={<EyeOutlined />}
            unCheckedChildren={<EyeInvisibleOutlined />}
          />
        </Tooltip>
      </Space>

      {/* Breadcrumb */}
      <Breadcrumb items={breadcrumbItems} className="mb-4" />

      {/* File table */}
      <FileTable
        files={filteredFiles}
        loading={loading}
        selectedFiles={selectedFiles}
        onSelectionChange={setSelectedFiles}
        onFileClick={handleFileClick}
        onRefresh={fetchFiles}
        currentPath={currentPath}
      />

      {/* Modals */}
      <CreateModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={() => {
          setCreateModalOpen(false)
          fetchFiles()
        }}
        isDirectory={createIsDirectory}
        currentPath={currentPath}
      />

      <UploadModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={() => {
          setUploadModalOpen(false)
          fetchFiles()
        }}
        currentPath={currentPath}
      />

      <FilePreview
        file={previewFile}
        onClose={() => setPreviewFile(null)}
        onRefresh={fetchFiles}
      />

      <MoveModal
        open={moveModalOpen}
        onClose={() => setMoveModalOpen(false)}
        onSuccess={() => {
          setMoveModalOpen(false)
          setSelectedFiles([])
          fetchFiles()
        }}
        files={selectedFiles}
        mode={moveMode}
      />
    </Card>
  )
}

export default Files
