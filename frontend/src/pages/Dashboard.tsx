import { useEffect, useState } from 'react'
import { StatisticCard } from '@ant-design/pro-components'
import { Row, Col, Card, Spin } from 'antd'
import {
  CloudServerOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import api from '../utils/api'

interface Stats {
  totalNodes: number
  onlineNodes: number
  totalDatasets: number
  totalJobs: number
  runningJobs: number
  completedJobs: number
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats>({
    totalNodes: 0,
    onlineNodes: 0,
    totalDatasets: 0,
    totalJobs: 0,
    runningJobs: 0,
    completedJobs: 0,
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [nodesRes, datasetsRes, jobsRes] = await Promise.all([
          api.get('/nodes/'),
          api.get('/datasets/'),
          api.get('/jobs/'),
        ])

        const nodes = nodesRes.data
        const datasets = datasetsRes.data
        const jobs = jobsRes.data

        setStats({
          totalNodes: nodes.length,
          onlineNodes: nodes.filter((n: any) => n.status === 'online').length,
          totalDatasets: datasets.length,
          totalJobs: jobs.length,
          runningJobs: jobs.filter((j: any) => j.status === 'running').length,
          completedJobs: jobs.filter((j: any) => j.status === 'completed').length,
        })
      } catch (error) {
        // Error handled by interceptor
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Dashboard</h2>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: 'Total Nodes',
              value: stats.totalNodes,
              icon: <CloudServerOutlined className="text-blue-500" />,
            }}
            chart={<div className="text-sm text-gray-500">{stats.onlineNodes} online</div>}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: 'Total Datasets',
              value: stats.totalDatasets,
              icon: <DatabaseOutlined className="text-green-500" />,
            }}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: 'Total Jobs',
              value: stats.totalJobs,
              icon: <PlayCircleOutlined className="text-orange-500" />,
            }}
            chart={<div className="text-sm text-gray-500">{stats.runningJobs} running</div>}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: 'Completed Jobs',
              value: stats.completedJobs,
              icon: <CheckCircleOutlined className="text-emerald-500" />,
            }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-6">
        <Col span={24}>
          <Card title="Quick Start Guide">
            <ul className="list-disc list-inside space-y-2">
              <li>
                Register worker nodes in the <strong>Nodes</strong> section
              </li>
              <li>
                Add datasets to your nodes in the <strong>Datasets</strong> section
              </li>
              <li>
                Submit ML training jobs in the <strong>Jobs</strong> section
              </li>
              <li>Monitor job status and view logs in real-time</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
