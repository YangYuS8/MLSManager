import { useNodeContext } from '../contexts/NodeContext'

/**
 * Hook to get the current selected node
 */
export const useCurrentNode = () => {
  const { currentNode, setCurrentNode, loading } = useNodeContext()
  return { currentNode, setCurrentNode, loading }
}

/**
 * Hook to get all available nodes
 */
export const useAvailableNodes = () => {
  const { availableNodes, onlineNodes, loading, refreshNodes } = useNodeContext()
  return { availableNodes, onlineNodes, loading, refreshNodes }
}

export default useCurrentNode
