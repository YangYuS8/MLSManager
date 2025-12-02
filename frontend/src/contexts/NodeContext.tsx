import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { listNodesApiV1NodesGet, type NodeRead } from '../api/client'

const NODE_STORAGE_KEY = 'mlsmanager_current_node_id'

interface NodeContextType {
  currentNode: NodeRead | null
  setCurrentNode: (node: NodeRead | null) => void
  availableNodes: NodeRead[]
  onlineNodes: NodeRead[]
  loading: boolean
  refreshNodes: () => Promise<void>
}

const NodeContext = createContext<NodeContextType | undefined>(undefined)

export const useNodeContext = (): NodeContextType => {
  const context = useContext(NodeContext)
  if (!context) {
    throw new Error('useNodeContext must be used within a NodeProvider')
  }
  return context
}

interface NodeProviderProps {
  children: ReactNode
}

export const NodeProvider: React.FC<NodeProviderProps> = ({ children }) => {
  const [currentNode, setCurrentNodeState] = useState<NodeRead | null>(null)
  const [availableNodes, setAvailableNodes] = useState<NodeRead[]>([])
  const [loading, setLoading] = useState(false)

  // Filter online nodes
  const onlineNodes = availableNodes.filter((node) => node.status === 'online')

  // Load nodes from API
  const refreshNodes = useCallback(async () => {
    setLoading(true)
    try {
      const response = await listNodesApiV1NodesGet()
      const nodes = response.data || []
      setAvailableNodes(nodes)

      // Restore previously selected node
      const savedNodeId = localStorage.getItem(NODE_STORAGE_KEY)
      if (savedNodeId && !currentNode) {
        const savedNode = nodes.find((n) => String(n.id) === savedNodeId)
        if (savedNode && savedNode.status === 'online') {
          setCurrentNodeState(savedNode)
        } else {
          // If saved node is offline or not found, clear storage
          localStorage.removeItem(NODE_STORAGE_KEY)
          // Auto-select master node or first online node
          const masterNode = nodes.find((n) => n.node_type === 'master' && n.status === 'online')
          const firstOnline = nodes.find((n) => n.status === 'online')
          if (masterNode) {
            setCurrentNodeState(masterNode)
          } else if (firstOnline) {
            setCurrentNodeState(firstOnline)
          }
        }
      } else if (!currentNode && nodes.length > 0) {
        // First load, select master or first online node
        const masterNode = nodes.find((n) => n.node_type === 'master' && n.status === 'online')
        const firstOnline = nodes.find((n) => n.status === 'online')
        if (masterNode) {
          setCurrentNodeState(masterNode)
        } else if (firstOnline) {
          setCurrentNodeState(firstOnline)
        }
      }
    } catch (error) {
      console.error('Failed to fetch nodes:', error)
    } finally {
      setLoading(false)
    }
  }, [currentNode])

  // Set current node with persistence
  const setCurrentNode = useCallback((node: NodeRead | null) => {
    setCurrentNodeState(node)
    if (node) {
      localStorage.setItem(NODE_STORAGE_KEY, String(node.id))
    } else {
      localStorage.removeItem(NODE_STORAGE_KEY)
    }
  }, [])

  // Initial load
  useEffect(() => {
    refreshNodes()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Check if current node goes offline
  useEffect(() => {
    if (currentNode) {
      const nodeInList = availableNodes.find((n) => n.id === currentNode.id)
      if (nodeInList && nodeInList.status !== 'online') {
        // Current node went offline, clear selection
        setCurrentNode(null)
      }
    }
  }, [availableNodes, currentNode, setCurrentNode])

  return (
    <NodeContext.Provider
      value={{
        currentNode,
        setCurrentNode,
        availableNodes,
        onlineNodes,
        loading,
        refreshNodes,
      }}
    >
      {children}
    </NodeContext.Provider>
  )
}

export default NodeContext
