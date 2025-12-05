import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  UserOutlined,
  LogoutOutlined,
  FolderOutlined,
  SettingOutlined,
  CodeOutlined,
  ProfileOutlined,
} from '@ant-design/icons'
import { ProLayout, ProLayoutProps } from '@ant-design/pro-components'
import { Dropdown } from 'antd'
import { useTranslation } from 'react-i18next'
import { removeToken, getUsername, getUserRole } from '../utils/auth'
import { LanguageSwitcher } from '../components/LanguageSwitcher'
import NodeSelector from '../components/NodeSelector'

interface BasicLayoutProps {
  onLogout: () => void
}

const BasicLayout: React.FC<BasicLayoutProps> = ({ onLogout }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const username = getUsername()
  const userRole = getUserRole()
  const { t } = useTranslation()

  const menuItems = [
    {
      path: '/dashboard',
      name: t('nav.dashboard'),
      icon: <DashboardOutlined />,
    },
    {
      path: '/nodes',
      name: t('nav.nodes'),
      icon: <CloudServerOutlined />,
    },
    {
      path: '/datasets',
      name: t('nav.datasets'),
      icon: <DatabaseOutlined />,
    },
    {
      path: '/jobs',
      name: t('nav.jobs'),
      icon: <PlayCircleOutlined />,
    },
    {
      path: '/files',
      name: t('nav.files'),
      icon: <FolderOutlined />,
    },
    {
      path: '/projects',
      name: t('nav.projects') || 'Projects',
      icon: <CodeOutlined />,
    },
    {
      path: '/users',
      name: t('nav.users'),
      icon: <UserOutlined />,
    },
    // Only show settings menu for superadmin
    ...(userRole === 'superadmin'
      ? [
          {
            path: '/settings',
            name: t('nav.settings'),
            icon: <SettingOutlined />,
          },
        ]
      : []),
  ]

  const handleLogout = () => {
    removeToken()
    onLogout()
    navigate('/login')
  }

  const layoutSettings: ProLayoutProps = {
    title: 'ML Server Manager',
    logo: '/logo.svg',
    layout: 'mix',
    splitMenus: false,
    fixedHeader: true,
    fixSiderbar: true,
    route: {
      routes: menuItems,
    },
    location: {
      pathname: location.pathname,
    },
    menuItemRender: (item, dom) => <div onClick={() => navigate(item.path || '/')}>{dom}</div>,
    actionsRender: () => [
      <NodeSelector key="node" />,
      <LanguageSwitcher key="lang" />,
    ],
    avatarProps: {
      src: undefined,
      title: username || 'User',
      render: (_, dom) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'profile',
                icon: <ProfileOutlined />,
                label: t('profile.title'),
                onClick: () => navigate('/profile'),
              },
              {
                type: 'divider',
              },
              {
                key: 'logout',
                icon: <LogoutOutlined />,
                label: t('auth.logout'),
                onClick: handleLogout,
              },
            ],
          }}
        >
          {dom}
        </Dropdown>
      ),
    },
  }

  return (
    <ProLayout {...layoutSettings}>
      <div className="p-4">
        <Outlet />
      </div>
    </ProLayout>
  )
}

export default BasicLayout
