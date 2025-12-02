import { useTranslation } from 'react-i18next'
import { Table, Space, Tag, Tooltip } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  FolderOutlined,
  FileOutlined,
  FileTextOutlined,
  FileImageOutlined,
  FileZipOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FileMarkdownOutlined,
  CodeOutlined,
} from '@ant-design/icons'
import type { FileInfo } from '../../../api/client'

interface FileTableProps {
  files: FileInfo[]
  loading: boolean
  selectedFiles: FileInfo[]
  onSelectionChange: (files: FileInfo[]) => void
  onFileClick: (file: FileInfo) => void
  onRefresh: () => void
  currentPath: string
}

const FileTable: React.FC<FileTableProps> = ({
  files,
  loading,
  selectedFiles,
  onSelectionChange,
  onFileClick,
}) => {
  const { t } = useTranslation()

  // Get file icon based on type and extension
  const getFileIcon = (file: FileInfo) => {
    if (file.type === 'directory') {
      return <FolderOutlined style={{ color: '#faad14', fontSize: 18 }} />
    }

    const ext = file.extension?.toLowerCase()
    const iconStyle = { fontSize: 18 }

    // Code files
    if (
      ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'c', 'cpp', 'h', 'go', 'rs', 'rb', 'php', 'sh', 'bash'].includes(
        ext || ''
      )
    ) {
      return <CodeOutlined style={{ ...iconStyle, color: '#52c41a' }} />
    }

    // Markdown
    if (['md', 'mdx'].includes(ext || '')) {
      return <FileMarkdownOutlined style={{ ...iconStyle, color: '#1890ff' }} />
    }

    // Text files
    if (['txt', 'log', 'csv', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf'].includes(ext || '')) {
      return <FileTextOutlined style={{ ...iconStyle, color: '#8c8c8c' }} />
    }

    // Images
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'].includes(ext || '')) {
      return <FileImageOutlined style={{ ...iconStyle, color: '#eb2f96' }} />
    }

    // Archives
    if (['zip', 'tar', 'gz', 'bz2', 'rar', '7z', 'xz'].includes(ext || '')) {
      return <FileZipOutlined style={{ ...iconStyle, color: '#faad14' }} />
    }

    // PDF
    if (ext === 'pdf') {
      return <FilePdfOutlined style={{ ...iconStyle, color: '#f5222d' }} />
    }

    // Excel
    if (['xls', 'xlsx'].includes(ext || '')) {
      return <FileExcelOutlined style={{ ...iconStyle, color: '#52c41a' }} />
    }

    // Word
    if (['doc', 'docx'].includes(ext || '')) {
      return <FileWordOutlined style={{ ...iconStyle, color: '#1890ff' }} />
    }

    return <FileOutlined style={iconStyle} />
  }

  // Format file size
  const formatSize = (size: number) => {
    if (size === 0) return '-'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let unitIndex = 0
    let displaySize = size
    while (displaySize >= 1024 && unitIndex < units.length - 1) {
      displaySize /= 1024
      unitIndex++
    }
    return `${displaySize.toFixed(unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  const columns: ColumnsType<FileInfo> = [
    {
      title: t('files.name'),
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name: string, record) => (
        <Space
          className="cursor-pointer hover:text-blue-500"
          onClick={() => onFileClick(record)}
        >
          {getFileIcon(record)}
          <span className={record.is_hidden ? 'text-gray-400' : ''}>
            {name}
          </span>
          {record.type === 'symlink' && (
            <Tag color="purple" className="text-xs">
              {t('files.symlink')}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: t('files.size'),
      dataIndex: 'size',
      key: 'size',
      width: 100,
      sorter: (a, b) => (a.size ?? 0) - (b.size ?? 0),
      render: (size: number, record) =>
        record.type === 'directory' ? '-' : formatSize(size),
    },
    {
      title: t('files.permissions'),
      dataIndex: 'mode',
      key: 'mode',
      width: 120,
      render: (mode: string, record) => (
        <Tooltip title={`${mode} (${record.mode_octal})`}>
          <code className="text-xs">{record.mode_octal}</code>
        </Tooltip>
      ),
    },
    {
      title: t('files.owner'),
      dataIndex: 'owner',
      key: 'owner',
      width: 100,
      render: (owner: string, record) => (
        <span className="text-gray-500">
          {owner}:{record.group}
        </span>
      ),
    },
    {
      title: t('files.modified'),
      dataIndex: 'modified_at',
      key: 'modified_at',
      width: 180,
      sorter: (a, b) =>
        new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime(),
      render: (date: string) => (
        <span className="text-gray-500">{formatDate(date)}</span>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={files}
      loading={loading}
      rowKey="path"
      size="small"
      rowSelection={{
        selectedRowKeys: selectedFiles.map((f) => f.path),
        onChange: (_, rows) => onSelectionChange(rows),
      }}
      pagination={{
        pageSize: 50,
        showSizeChanger: true,
        showTotal: (total) => t('files.totalItems', { count: total }),
      }}
      onRow={(record) => ({
        onDoubleClick: () => onFileClick(record),
      })}
    />
  )
}

export default FileTable
