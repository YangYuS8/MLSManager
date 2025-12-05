import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  Typography,
  message,
  Spin,
  Tag,
  Alert,
} from 'antd'
import {
  UserOutlined,
  MailOutlined,
  SafetyOutlined,
  LockOutlined,
  GithubOutlined,
  LinkOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { getToken } from '../utils/auth'

const { Title, Text } = Typography

interface UserProfile {
  id: number
  username: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const Profile: React.FC = () => {
  const { t } = useTranslation()
  const [profileForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [savingProfile, setSavingProfile] = useState(false)
  const [savingPassword, setSavingPassword] = useState(false)

  const fetchProfile = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/users/me', {
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setProfile(data)
        profileForm.setFieldsValue({
          username: data.username,
          email: data.email,
          full_name: data.full_name || '',
        })
      }
    } catch (err) {
      console.error('Failed to fetch profile:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  const handleUpdateProfile = async (values: Record<string, string>) => {
    setSavingProfile(true)
    try {
      const response = await fetch('/api/v1/users/me', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          email: values.email,
          full_name: values.full_name || null,
        }),
      })

      if (response.ok) {
        message.success(t('profile.updateSuccess'))
        fetchProfile()
      } else {
        const error = await response.json()
        message.error(error.detail || t('profile.updateFailed'))
      }
    } catch (err) {
      message.error(t('profile.updateFailed'))
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async (values: Record<string, string>) => {
    if (values.new_password !== values.confirm_password) {
      message.error(t('profile.passwordMismatch'))
      return
    }

    setSavingPassword(true)
    try {
      const response = await fetch('/api/v1/users/me/password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          current_password: values.current_password,
          new_password: values.new_password,
        }),
      })

      if (response.ok) {
        message.success(t('profile.passwordChangeSuccess'))
        passwordForm.resetFields()
      } else {
        const error = await response.json()
        if (error.detail === 'Incorrect current password') {
          message.error(t('profile.incorrectPassword'))
        } else {
          message.error(error.detail || t('profile.passwordChangeFailed'))
        }
      }
    } catch (err) {
      message.error(t('profile.passwordChangeFailed'))
    } finally {
      setSavingPassword(false)
    }
  }

  const getRoleTag = (role: string) => {
    const roleConfig: Record<string, { color: string; label: string }> = {
      superadmin: { color: 'red', label: t('users.roles.superadmin') },
      admin: { color: 'blue', label: t('users.roles.admin') },
      member: { color: 'default', label: t('users.roles.member') },
    }
    const config = roleConfig[role] || roleConfig.member
    return <Tag color={config.color}>{config.label}</Tag>
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <Title level={3}>
          <UserOutlined className="mr-2" />
          {t('profile.title')}
        </Title>
        <Text type="secondary">{t('profile.subtitle')}</Text>
      </div>

      {/* Basic Info Card */}
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <UserOutlined className="text-lg mr-2" />
          <Title level={5} className="m-0">
            {t('profile.basicInfo')}
          </Title>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded">
          <Space size="large">
            <div>
              <Text type="secondary">{t('profile.role')}: </Text>
              {profile && getRoleTag(profile.role)}
            </div>
            <div>
              <Text type="secondary">{t('profile.createdAt')}: </Text>
              <Text>{profile && new Date(profile.created_at).toLocaleDateString()}</Text>
            </div>
          </Space>
        </div>

        <Form
          form={profileForm}
          layout="vertical"
          onFinish={handleUpdateProfile}
        >
          <Form.Item
            name="username"
            label={t('profile.username')}
            extra={t('profile.usernameHint')}
          >
            <Input prefix={<UserOutlined />} disabled />
          </Form.Item>

          <Form.Item
            name="email"
            label={t('profile.email')}
            rules={[
              { required: true, message: t('auth.email') },
              { type: 'email', message: t('errors.validationError') },
            ]}
          >
            <Input prefix={<MailOutlined />} />
          </Form.Item>

          <Form.Item name="full_name" label={t('profile.fullName')}>
            <Input prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={savingProfile}>
              {t('common.save')}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Password Change Card */}
      <Card className="mb-4">
        <div className="flex items-center mb-4">
          <SafetyOutlined className="text-lg mr-2" />
          <Title level={5} className="m-0">
            {t('profile.changePassword')}
          </Title>
        </div>

        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="current_password"
            label={t('profile.currentPassword')}
            rules={[{ required: true }]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>

          <Form.Item
            name="new_password"
            label={t('profile.newPassword')}
            rules={[
              { required: true },
              { min: 8, message: 'Password must be at least 8 characters' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label={t('profile.confirmPassword')}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error(t('profile.passwordMismatch')))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={savingPassword}>
              {t('profile.changePassword')}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* OAuth Connections Card */}
      <Card>
        <div className="flex items-center mb-4">
          <LinkOutlined className="text-lg mr-2" />
          <Title level={5} className="m-0">
            {t('profile.oauth')}
          </Title>
        </div>

        <Alert
          message={t('profile.oauthNotConfigured')}
          type="info"
          showIcon
          className="mb-4"
        />

        <div className="space-y-3">
          {/* GitHub */}
          <div className="flex items-center justify-between p-3 border rounded">
            <Space>
              <GithubOutlined className="text-xl" />
              <Text strong>{t('profile.github')}</Text>
            </Space>
            <Space>
              <Tag icon={<CloseCircleOutlined />} color="default">
                {t('profile.notBound')}
              </Tag>
              <Button size="small" disabled>
                {t('profile.bindAccount')}
              </Button>
            </Space>
          </div>

          {/* Gitee */}
          <div className="flex items-center justify-between p-3 border rounded">
            <Space>
              <svg className="w-5 h-5" viewBox="0 0 1024 1024">
                <path
                  fill="currentColor"
                  d="M512 1024C230.4 1024 0 793.6 0 512S230.4 0 512 0s512 230.4 512 512-230.4 512-512 512z m259.2-569.6H480c-12.8 0-25.6 12.8-25.6 25.6v64c0 12.8 12.8 25.6 25.6 25.6h176c12.8 0 25.6 12.8 25.6 25.6v12.8c0 41.6-35.2 76.8-76.8 76.8h-240c-12.8 0-25.6-12.8-25.6-25.6V416c0-41.6 35.2-76.8 76.8-76.8h355.2c12.8 0 25.6-12.8 25.6-25.6v-64c0-12.8-12.8-25.6-25.6-25.6H416c-105.6 0-192 86.4-192 192v291.2c0 12.8 12.8 25.6 25.6 25.6h320c92.8 0 169.6-76.8 169.6-169.6V480c0-12.8-12.8-25.6-25.6-25.6z"
                />
              </svg>
              <Text strong>{t('profile.gitee')}</Text>
            </Space>
            <Space>
              <Tag icon={<CloseCircleOutlined />} color="default">
                {t('profile.notBound')}
              </Tag>
              <Button size="small" disabled>
                {t('profile.bindAccount')}
              </Button>
            </Space>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default Profile
