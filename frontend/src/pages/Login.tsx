import { useState } from 'react'
import { LoginForm, ProFormText } from '@ant-design/pro-components'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { message } from 'antd'
import api from '../utils/api'
import { setToken, setUsername } from '../utils/auth'

interface LoginProps {
  onLoginSuccess: () => void
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const formData = new URLSearchParams()
      formData.append('username', values.username)
      formData.append('password', values.password)

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      setToken(response.data.access_token)
      setUsername(values.username)
      message.success('Login successful')
      onLoginSuccess()
    } catch (error) {
      // Error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md">
        <LoginForm
          title="ML Server Manager"
          subTitle="Multi-node ML workspace & job management system"
          onFinish={handleSubmit}
          loading={loading}
        >
          <ProFormText
            name="username"
            fieldProps={{
              size: 'large',
              prefix: <UserOutlined />,
            }}
            placeholder="Username"
            rules={[
              {
                required: true,
                message: 'Please enter your username',
              },
            ]}
          />
          <ProFormText.Password
            name="password"
            fieldProps={{
              size: 'large',
              prefix: <LockOutlined />,
            }}
            placeholder="Password"
            rules={[
              {
                required: true,
                message: 'Please enter your password',
              },
            ]}
          />
        </LoginForm>
      </div>
    </div>
  )
}

export default Login
