import { useTranslation } from 'react-i18next'
import { Dropdown, Space, Badge, Spin, Button, Empty } from 'antd'
import type { MenuProps } from 'antd'
import {
  CloudServerOutlined,
  DownOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useNodeContext } from '../../contexts/NodeContext'

const NodeSelector: React.FC = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { currentNode, setCurrentNode, availableNodes, loading, refreshNodes } = useNodeContext()

  // Get status badge color
  const getStatusColor = (status: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (status) {
      case 'online':
        return 'success'
      case 'busy':
        return 'warning'
      case 'offline':
        return 'error'
      default:
        return 'default'
    }
  }

  // Build menu items
  const buildMenuItems = (): MenuProps['items'] => {
    if (availableNodes.length === 0) {
      return [
        {
          key: 'empty',
          label: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={t('nodeSelector.noNodes')}
              className="py-2"
            />
          ),
          disabled: true,
        },
      ]
    }

    const nodeItems: MenuProps['items'] = availableNodes.map((node) => ({
      key: node.id,
      label: (
        <div className="flex items-center justify-between min-w-[200px]">
          <div className="flex items-center gap-2">
            <Badge status={getStatusColor(node.status)} />
            <span>{node.name}</span>
            {node.node_type === 'master' && (
              <span className="text-xs text-blue-500 bg-blue-50 px-1 rounded">
                {t('nodeSelector.master')}
              </span>
            )}
          </div>
          <span className="text-xs text-gray-400">{node.host}</span>
        </div>
      ),
      disabled: node.status !== 'online',
      onClick: () => {
        if (node.status === 'online') {
          setCurrentNode(node)
        }
      },
    }))

    return [
      ...nodeItems,
      { type: 'divider' as const },
      {
        key: 'refresh',
        icon: <ReloadOutlined />,
        label: t('nodeSelector.refresh'),
        onClick: () => refreshNodes(),
      },
      {
        key: 'manage',
        icon: <SettingOutlined />,
        label: t('nodeSelector.manageNodes'),
        onClick: () => navigate('/nodes'),
      },
    ]
  }

  // Render current node display
  const renderCurrentNode = () => {
    if (loading) {
      return <Spin size="small" />
    }

    if (!currentNode) {
      return (
        <Space>
          <CloudServerOutlined />
          <span>{t('nodeSelector.selectNode')}</span>
          <DownOutlined />
        </Space>
      )
    }

    return (
      <Space>
        <Badge status={getStatusColor(currentNode.status)} />
        <CloudServerOutlined />
        <span className="max-w-[120px] truncate">{currentNode.name}</span>
        {currentNode.node_type === 'master' && (
          <span className="text-xs text-blue-500">★</span>
        )}
        <DownOutlined />
      </Space>
    )
  }

  return (
    <Dropdown
      menu={{ items: buildMenuItems() }}
      trigger={['click']}
      placement="bottomRight"
    >
      <Button
        type="text"
        className="flex items-center h-10 px-3 hover:bg-gray-100 rounded-md"
      >
        {renderCurrentNode()}
      </Button>
    </Dropdown>
  )
}

export default NodeSelector
