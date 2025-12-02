import { useState } from 'react'
import { LoginForm, ProFormText } from '@ant-design/pro-components'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { message } from 'antd'
import { useTranslation } from 'react-i18next'
import { loginApiV1AuthLoginPost } from '../api/client'
import { setToken, setUsername } from '../utils/auth'
import { LanguageSwitcher } from '../components/LanguageSwitcher'

interface LoginProps {
  onLoginSuccess: () => void
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false)
  const { t } = useTranslation()

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const { data, error } = await loginApiV1AuthLoginPost({
        body: {
          username: values.username,
          password: values.password,
        },
      })

      if (error) {
        message.error((error as { detail?: string }).detail || t('auth.loginFailed'))
        return
      }

      if (data) {
        setToken(data.access_token)
        setUsername(values.username)
        message.success(t('auth.loginSuccess'))
        onLoginSuccess()
      }
    } catch (err) {
      message.error(t('errors.networkError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 relative">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>
      <div className="w-full max-w-md">
        <LoginForm
          title="ML Server Manager"
          subTitle={t('auth.signInToContinue')}
          onFinish={handleSubmit}
          loading={loading}
          submitter={{
            searchConfig: {
              submitText: t('auth.login'),
            },
          }}
        >
          <ProFormText
            name="username"
            fieldProps={{
              size: 'large',
              prefix: <UserOutlined />,
            }}
            placeholder={t('auth.username')}
            rules={[
              {
                required: true,
                message: t('auth.username'),
              },
            ]}
          />
          <ProFormText.Password
            name="password"
            fieldProps={{
              size: 'large',
              prefix: <LockOutlined />,
            }}
            placeholder={t('auth.password')}
            rules={[
              {
                required: true,
                message: t('auth.password'),
              },
            ]}
          />
        </LoginForm>
      </div>
    </div>
  )
}

export default Login
