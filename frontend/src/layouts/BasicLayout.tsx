import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { ProLayout, ProLayoutProps } from '@ant-design/pro-components'
import { Dropdown, Avatar } from 'antd'
import { removeToken, getUsername } from '../utils/auth'

interface BasicLayoutProps {
  onLogout: () => void
}

const menuItems = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    icon: <DashboardOutlined />,
  },
  {
    path: '/nodes',
    name: 'Nodes',
    icon: <CloudServerOutlined />,
  },
  {
    path: '/datasets',
    name: 'Datasets',
    icon: <DatabaseOutlined />,
  },
  {
    path: '/jobs',
    name: 'Jobs',
    icon: <PlayCircleOutlined />,
  },
  {
    path: '/users',
    name: 'Users',
    icon: <UserOutlined />,
  },
]

const BasicLayout: React.FC<BasicLayoutProps> = ({ onLogout }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const username = getUsername()

  const handleLogout = () => {
    removeToken()
    onLogout()
    navigate('/login')
  }

  const layoutSettings: ProLayoutProps = {
    title: 'ML Server Manager',
    logo: '/vite.svg',
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
    avatarProps: {
      src: undefined,
      title: username || 'User',
      render: (_, dom) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'logout',
                icon: <LogoutOutlined />,
                label: 'Logout',
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
