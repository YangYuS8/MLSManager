import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Switch,
  Button,
  Select,
  InputNumber,
  Space,
  Divider,
  Typography,
  message,
  Alert,
  Popconfirm,
  Spin,
  ColorPicker,
} from 'antd'
import type { Color } from 'antd/es/color-picker'
import {
  SaveOutlined,
  ReloadOutlined,
  SettingOutlined,
  AppstoreOutlined,
  SafetyOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { getToken } from '../utils/auth'

const { Title, Text } = Typography
const { TextArea } = Input

interface Settings {
  site_name: string
  site_description: string
  primary_color: string
  dark_mode: string
  allow_registration: string
  max_upload_size_mb: string
  default_user_role: string
  maintenance_mode: string
  announcement: string
  logo_url: string
}

const defaultSettings: Settings = {
  site_name: 'ML Server Manager',
  site_description: '',
  primary_color: '#1890ff',
  dark_mode: 'false',
  allow_registration: 'true',
  max_upload_size_mb: '100',
  default_user_role: 'member',
  maintenance_mode: 'false',
  announcement: '',
  logo_url: '/logo.svg',
}

const Settings: React.FC = () => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [settings, setSettings] = useState<Settings>(defaultSettings)

  const fetchSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/settings', {
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })
      if (response.status === 403) {
        setError(t('settings.accessDenied'))
        return
      }
      if (!response.ok) {
        throw new Error('Failed to fetch settings')
      }
      const data = await response.json()
      const loadedSettings = { ...defaultSettings, ...data.settings }
      setSettings(loadedSettings)
      form.setFieldsValue({
        site_name: loadedSettings.site_name,
        site_description: loadedSettings.site_description,
        primary_color: loadedSettings.primary_color,
        dark_mode: loadedSettings.dark_mode === 'true',
        allow_registration: loadedSettings.allow_registration === 'true',
        max_upload_size_mb: parseInt(loadedSettings.max_upload_size_mb) || 100,
        default_user_role: loadedSettings.default_user_role,
        maintenance_mode: loadedSettings.maintenance_mode === 'true',
        announcement: loadedSettings.announcement,
        logo_url: loadedSettings.logo_url,
      })
    } catch (err) {
      console.error('Failed to fetch settings:', err)
      setError(t('settings.loadFailed'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSettings()
  }, [])

  const handleSave = async (values: Record<string, unknown>) => {
    setSaving(true)
    try {
      // Convert form values to settings format
      const colorValue = values.primary_color
      let primaryColor = '#1890ff'
      if (colorValue) {
        if (typeof colorValue === 'string') {
          primaryColor = colorValue
        } else if (typeof colorValue === 'object' && colorValue !== null) {
          // It's a Color object from ColorPicker
          primaryColor = (colorValue as Color).toHexString()
        }
      }

      const settingsToSave: Record<string, string> = {
        site_name: values.site_name as string,
        site_description: values.site_description as string,
        primary_color: primaryColor,
        dark_mode: values.dark_mode ? 'true' : 'false',
        allow_registration: values.allow_registration ? 'true' : 'false',
        max_upload_size_mb: String(values.max_upload_size_mb),
        default_user_role: values.default_user_role as string,
        maintenance_mode: values.maintenance_mode ? 'true' : 'false',
        announcement: (values.announcement as string) || '',
        logo_url: values.logo_url as string,
      }

      const response = await fetch('/api/v1/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ settings: settingsToSave }),
      })

      if (!response.ok) {
        throw new Error('Failed to save settings')
      }

      message.success(t('settings.saveSuccess'))
      await fetchSettings()
    } catch (err) {
      console.error('Failed to save settings:', err)
      message.error(t('settings.saveFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    setSaving(true)
    try {
      const response = await fetch('/api/v1/settings/reset', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to reset settings')
      }

      message.success(t('settings.resetSuccess'))
      await fetchSettings()
    } catch (err) {
      console.error('Failed to reset settings:', err)
      message.error(t('settings.resetFailed'))
    } finally {
      setSaving(false)
    }
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert
          type="error"
          message={error}
          showIcon
          action={
            <Button type="link" onClick={fetchSettings}>
              {t('common.reset')}
            </Button>
          }
        />
      </div>
    )
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
          <SettingOutlined className="mr-2" />
          {t('settings.title')}
        </Title>
        <Text type="secondary">{t('settings.subtitle')}</Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={{
          site_name: settings.site_name,
          site_description: settings.site_description,
          primary_color: settings.primary_color,
          dark_mode: settings.dark_mode === 'true',
          allow_registration: settings.allow_registration === 'true',
          max_upload_size_mb: parseInt(settings.max_upload_size_mb) || 100,
          default_user_role: settings.default_user_role,
          maintenance_mode: settings.maintenance_mode === 'true',
          announcement: settings.announcement,
          logo_url: settings.logo_url,
        }}
      >
        {/* General Settings */}
        <Card className="mb-4">
          <div className="flex items-center mb-4">
            <AppstoreOutlined className="text-lg mr-2" />
            <Title level={5} className="m-0">
              {t('settings.general')}
            </Title>
          </div>

          <Form.Item
            name="site_name"
            label={t('settings.siteName')}
            extra={t('settings.siteNameHint')}
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="site_description"
            label={t('settings.siteDescription')}
            extra={t('settings.siteDescriptionHint')}
          >
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item
            name="logo_url"
            label={t('settings.logoUrl')}
            extra={t('settings.logoUrlHint')}
          >
            <Input />
          </Form.Item>
        </Card>

        {/* Appearance Settings */}
        <Card className="mb-4">
          <div className="flex items-center mb-4">
            <AppstoreOutlined className="text-lg mr-2" />
            <Title level={5} className="m-0">
              {t('settings.appearance')}
            </Title>
          </div>

          <Form.Item
            name="primary_color"
            label={t('settings.primaryColor')}
            extra={t('settings.primaryColorHint')}
          >
            <ColorPicker format="hex" showText />
          </Form.Item>

          <Form.Item
            name="dark_mode"
            label={t('settings.darkMode')}
            valuePropName="checked"
            extra={t('settings.darkModeHint')}
          >
            <Switch />
          </Form.Item>
        </Card>

        {/* Security Settings */}
        <Card className="mb-4">
          <div className="flex items-center mb-4">
            <SafetyOutlined className="text-lg mr-2" />
            <Title level={5} className="m-0">
              {t('settings.security')}
            </Title>
          </div>

          <Form.Item
            name="allow_registration"
            label={t('settings.allowRegistration')}
            valuePropName="checked"
            extra={t('settings.allowRegistrationHint')}
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="default_user_role"
            label={t('settings.defaultUserRole')}
            extra={t('settings.defaultUserRoleHint')}
          >
            <Select>
              <Select.Option value="member">{t('users.roles.member')}</Select.Option>
              <Select.Option value="admin">{t('users.roles.admin')}</Select.Option>
            </Select>
          </Form.Item>
        </Card>

        {/* System Settings */}
        <Card className="mb-4">
          <div className="flex items-center mb-4">
            <ToolOutlined className="text-lg mr-2" />
            <Title level={5} className="m-0">
              {t('settings.system')}
            </Title>
          </div>

          <Form.Item
            name="max_upload_size_mb"
            label={t('settings.maxUploadSizeMb')}
            extra={t('settings.maxUploadSizeHint')}
          >
            <InputNumber min={1} max={10240} addonAfter="MB" style={{ width: 150 }} />
          </Form.Item>

          <Form.Item
            name="maintenance_mode"
            label={t('settings.maintenanceMode')}
            valuePropName="checked"
            extra={t('settings.maintenanceModeHint')}
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="announcement"
            label={t('settings.announcement')}
            extra={t('settings.announcementHint')}
          >
            <TextArea rows={3} />
          </Form.Item>
        </Card>

        <Divider />

        <div className="flex justify-between">
          <Popconfirm
            title={t('settings.resetConfirm')}
            onConfirm={handleReset}
            okText={t('common.yes')}
            cancelText={t('common.no')}
          >
            <Button icon={<ReloadOutlined />} danger>
              {t('settings.resetToDefaults')}
            </Button>
          </Popconfirm>

          <Space>
            <Button onClick={() => form.resetFields()}>{t('common.reset')}</Button>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving}>
              {t('common.save')}
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  )
}

export default Settings
