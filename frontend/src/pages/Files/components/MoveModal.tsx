import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Tree, Input, message, Spin } from 'antd'
import { FolderOutlined } from '@ant-design/icons'
import type { DataNode } from 'antd/es/tree'
import {
  listDirectoryApiV1FilesListGet,
  moveFileApiV1FilesMovePut,
  copyFileApiV1FilesCopyPut,
  type FileInfo,
} from '../../../api/client'

interface MoveModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  files: FileInfo[]
  mode: 'move' | 'copy'
}

const MoveModal: React.FC<MoveModalProps> = ({
  open,
  onClose,
  onSuccess,
  files,
  mode,
}) => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [treeData, setTreeData] = useState<DataNode[]>([])
  const [selectedPath, setSelectedPath] = useState<string>('/')
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>(['/'])
  const [loadedKeys, setLoadedKeys] = useState<React.Key[]>([])

  // Load root directory on open
  useEffect(() => {
    if (open) {
      loadDirectory('/')
    }
  }, [open])

  const loadDirectory = async (path: string): Promise<DataNode[]> => {
    try {
      const { data, error } = await listDirectoryApiV1FilesListGet({
        query: {
          path,
          show_hidden: false,
          sort_by: 'name',
          sort_order: 'asc',
        },
      })

      if (error) return []

      const directories = (data?.items || [])
        .filter((item) => item.type === 'directory')
        .map((dir) => ({
          key: dir.path,
          title: dir.name,
          icon: <FolderOutlined />,
          isLeaf: false,
        }))

      return directories
    } catch {
      return []
    }
  }

  // Initial load
  useEffect(() => {
    const initTree = async () => {
      setLoading(true)
      const children = await loadDirectory('/')
      setTreeData([
        {
          key: '/',
          title: '/',
          icon: <FolderOutlined />,
          children,
          isLeaf: false,
        },
      ])
      setLoadedKeys(['/'])
      setLoading(false)
    }

    if (open) {
      initTree()
    }
  }, [open])

  // Load children on expand
  const onLoadData = async (node: DataNode): Promise<void> => {
    if (loadedKeys.includes(node.key as string)) return

    const children = await loadDirectory(node.key as string)
    
    setTreeData((origin) =>
      updateTreeData(origin, node.key as string, children)
    )
    setLoadedKeys((prev) => [...prev, node.key as string])
  }

  const updateTreeData = (
    list: DataNode[],
    key: string,
    children: DataNode[]
  ): DataNode[] => {
    return list.map((node) => {
      if (node.key === key) {
        return { ...node, children }
      }
      if (node.children) {
        return { ...node, children: updateTreeData(node.children, key, children) }
      }
      return node
    })
  }

  const handleSubmit = async () => {
    if (!selectedPath) {
      message.warning(t('files.selectDestination'))
      return
    }

    // Check if trying to move into itself or its children
    const invalidMove = files.some((file) =>
      selectedPath.startsWith(file.path + '/') || selectedPath === file.path
    )
    if (invalidMove) {
      message.error(t('files.cannotMoveIntoSelf'))
      return
    }

    setSubmitting(true)
    let successCount = 0
    let errorCount = 0

    for (const file of files) {
      try {
        if (mode === 'move') {
          const { error } = await moveFileApiV1FilesMovePut({
            body: {
              source: file.path,
              destination: selectedPath,
              overwrite: false,
            },
          })
          if (error) {
            errorCount++
          } else {
            successCount++
          }
        } else {
          const { error } = await copyFileApiV1FilesCopyPut({
            body: {
              source: file.path,
              destination: selectedPath,
              overwrite: false,
            },
          })
          if (error) {
            errorCount++
          } else {
            successCount++
          }
        }
      } catch {
        errorCount++
      }
    }

    setSubmitting(false)

    if (successCount > 0) {
      message.success(
        mode === 'move'
          ? t('files.moveSuccess', { count: successCount })
          : t('files.copySuccess', { count: successCount })
      )
      onSuccess()
    }
    if (errorCount > 0) {
      message.error(
        mode === 'move'
          ? t('files.moveErrors', { count: errorCount })
          : t('files.copyErrors', { count: errorCount })
      )
    }
  }

  return (
    <Modal
      title={mode === 'move' ? t('files.moveTo') : t('files.copyTo')}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={submitting}
      width={500}
      destroyOnClose
    >
      <div className="mb-4">
        <strong>{t('files.selectedItems')}:</strong>
        <ul className="ml-4 mt-2 text-gray-600">
          {files.map((f) => (
            <li key={f.path}>• {f.name}</li>
          ))}
        </ul>
      </div>

      <div className="mb-2">
        <strong>{t('files.destination')}:</strong>
        <Input value={selectedPath} readOnly className="mt-1" />
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Spin />
        </div>
      ) : (
        <div className="border rounded p-2 max-h-64 overflow-auto">
          <Tree
            treeData={treeData}
            loadData={onLoadData}
            expandedKeys={expandedKeys}
            onExpand={(keys) => setExpandedKeys(keys)}
            selectedKeys={[selectedPath]}
            onSelect={(keys) => {
              if (keys.length > 0) {
                setSelectedPath(keys[0] as string)
              }
            }}
            showIcon
            blockNode
          />
        </div>
      )}
    </Modal>
  )
}

export default MoveModal
