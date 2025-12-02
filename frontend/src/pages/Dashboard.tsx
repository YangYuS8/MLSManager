import { useEffect, useState } from 'react'
import { StatisticCard } from '@ant-design/pro-components'
import { Row, Col, Card, Spin } from 'antd'
import {
  CloudServerOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listNodesApiV1NodesGet,
  listDatasetsApiV1DatasetsGet,
  listJobsApiV1JobsGet,
  type NodeRead,
  type DatasetRead,
  type JobRead,
} from '../api/client'

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
  const { t } = useTranslation()
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
          listNodesApiV1NodesGet(),
          listDatasetsApiV1DatasetsGet(),
          listJobsApiV1JobsGet(),
        ])

        const nodes: NodeRead[] = nodesRes.data || []
        const datasets: DatasetRead[] = datasetsRes.data || []
        const jobs: JobRead[] = jobsRes.data || []

        setStats({
          totalNodes: nodes.length,
          onlineNodes: nodes.filter((n) => n.status === 'online').length,
          totalDatasets: datasets.length,
          totalJobs: jobs.length,
          runningJobs: jobs.filter((j) => j.status === 'running').length,
          completedJobs: jobs.filter((j) => j.status === 'completed').length,
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
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
      <h2 className="text-2xl font-semibold mb-6">{t('dashboard.title')}</h2>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: t('dashboard.totalNodes'),
              value: stats.totalNodes,
              icon: <CloudServerOutlined className="text-blue-500" />,
            }}
            chart={
              <div className="text-sm text-gray-500">
                {stats.onlineNodes} {t('nodes.online').toLowerCase()}
              </div>
            }
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: t('dashboard.totalDatasets'),
              value: stats.totalDatasets,
              icon: <DatabaseOutlined className="text-green-500" />,
            }}
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: t('dashboard.totalJobs'),
              value: stats.totalJobs,
              icon: <PlayCircleOutlined className="text-orange-500" />,
            }}
            chart={
              <div className="text-sm text-gray-500">
                {stats.runningJobs} {t('dashboard.runningJobs').toLowerCase()}
              </div>
            }
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <StatisticCard
            statistic={{
              title: t('jobs.status.completed'),
              value: stats.completedJobs,
              icon: <CheckCircleOutlined className="text-emerald-500" />,
            }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-6">
        <Col span={24}>
          <Card title={t('dashboard.quickStats')}>
            <ul className="list-disc list-inside space-y-2">
              <li>
                {t('nav.nodes')}: <strong>{stats.totalNodes}</strong> ({stats.onlineNodes}{' '}
                {t('nodes.online').toLowerCase()})
              </li>
              <li>
                {t('nav.datasets')}: <strong>{stats.totalDatasets}</strong>
              </li>
              <li>
                {t('nav.jobs')}: <strong>{stats.totalJobs}</strong> ({stats.runningJobs}{' '}
                {t('dashboard.runningJobs').toLowerCase()})
              </li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
