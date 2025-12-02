import { useRef, useState } from 'react'
import {
  ProTable,
  ProColumns,
  ActionType,
  ModalForm,
  ProFormText,
  ProFormSelect,
} from '@ant-design/pro-components'
import { Tag, Button, message, Switch, Popconfirm } from 'antd'
import { PlusOutlined, ReloadOutlined, EditOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import {
  listUsersApiV1UsersGet,
  registerApiV1AuthRegisterPost,
  updateUserApiV1UsersUserIdPatch,
  type UserRead,
  type UserCreate,
  type UserUpdate,
} from '../api/client'

const roleColorMap: Record<string, string> = {
  superadmin: 'red',
  admin: 'orange',
  member: 'blue',
}

const Users: React.FC = () => {
  const { t } = useTranslation()
  const actionRef = useRef<ActionType>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null)

  const handleCreate = async (values: UserCreate) => {
    try {
      const { error } = await registerApiV1AuthRegisterPost({ body: values })
      if (error) {
        message.error(t('users.createFailed'))
        return false
      }
      message.success(t('users.createSuccess'))
      actionRef.current?.reload()
      return true
    } catch (err) {
      message.error(t('users.createFailed'))
      return false
    }
  }

  const handleUpdate = async (values: UserUpdate) => {
    if (!currentUser) return false
    try {
      const { error } = await updateUserApiV1UsersUserIdPatch({
        path: { user_id: currentUser.id },
        body: values,
      })
      if (error) {
        message.error(t('users.updateFailed'))
        return false
      }
      message.success(t('users.updateSuccess'))
      actionRef.current?.reload()
      return true
    } catch (err) {
      message.error(t('users.updateFailed'))
      return false
    }
  }

  const handleToggleActive = async (user: UserRead) => {
    try {
      const { error } = await updateUserApiV1UsersUserIdPatch({
        path: { user_id: user.id },
        body: { is_active: !user.is_active },
      })
      if (error) {
        message.error(t('users.statusUpdateFailed'))
        return
      }
      message.success(
        !user.is_active ? t('users.activated') : t('users.deactivated')
      )
      actionRef.current?.reload()
    } catch (err) {
      message.error(t('users.statusUpdateFailed'))
    }
  }

  const columns: ProColumns<UserRead>[] = [
    {
      title: t('users.username'),
      dataIndex: 'username',
      copyable: true,
    },
    {
      title: t('users.email'),
      dataIndex: 'email',
      copyable: true,
    },
    {
      title: t('users.fullName'),
      dataIndex: 'full_name',
      render: (text) => text || '-',
    },
    {
      title: t('users.role'),
      dataIndex: 'role',
      render: (_, record) => (
        <Tag color={roleColorMap[record.role] || 'default'}>
          {record.role.toUpperCase()}
        </Tag>
      ),
      width: 120,
    },
    {
      title: t('users.status'),
      dataIndex: 'is_active',
      render: (_, record) => (
        <Popconfirm
          title={
            record.is_active
              ? t('users.confirmDeactivate')
              : t('users.confirmActivate')
          }
          onConfirm={() => handleToggleActive(record)}
          okText={t('common.yes')}
          cancelText={t('common.no')}
        >
          <Switch
            checked={record.is_active}
            checkedChildren={t('users.active')}
            unCheckedChildren={t('users.inactive')}
          />
        </Popconfirm>
      ),
      width: 120,
    },
    {
      title: t('users.created'),
      dataIndex: 'created_at',
      valueType: 'dateTime',
      width: 160,
    },
    {
      title: t('common.actions'),
      valueType: 'option',
      width: 100,
      render: (_, record) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            setCurrentUser(record)
            setEditModalOpen(true)
          }}
        >
          {t('common.edit')}
        </Button>
      ),
    },
  ]

  return (
    <>
      <ProTable<UserRead>
        headerTitle={t('users.title')}
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async () => {
          const { data, error } = await listUsersApiV1UsersGet()
          if (error) {
            return { data: [], success: false, total: 0 }
          }
          return {
            data: data || [],
            success: true,
            total: data?.length || 0,
          }
        }}
        toolBarRender={() => [
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => actionRef.current?.reload()}
          >
            {t('common.refresh')}
          </Button>,
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
          >
            {t('users.addUser')}
          </Button>,
        ]}
        pagination={{
          pageSize: 10,
        }}
      />

      {/* Create User Modal */}
      <ModalForm<UserCreate>
        title={t('users.addUser')}
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={handleCreate}
        modalProps={{ destroyOnClose: true }}
        width={500}
      >
        <ProFormText
          name="username"
          label={t('users.username')}
          placeholder={t('users.enterUsername')}
          rules={[
            { required: true, message: t('users.usernameRequired') },
            { min: 3, message: t('users.usernameMinLength') },
          ]}
        />
        <ProFormText
          name="email"
          label={t('users.email')}
          placeholder={t('users.enterEmail')}
          rules={[
            { required: true, message: t('users.emailRequired') },
            { type: 'email', message: t('users.emailInvalid') },
          ]}
        />
        <ProFormText.Password
          name="password"
          label={t('users.password')}
          placeholder={t('users.enterPassword')}
          rules={[
            { required: true, message: t('users.passwordRequired') },
            { min: 6, message: t('users.passwordMinLength') },
          ]}
        />
        <ProFormText
          name="full_name"
          label={t('users.fullName')}
          placeholder={t('users.enterFullName')}
        />
        <ProFormSelect
          name="role"
          label={t('users.role')}
          initialValue="member"
          options={[
            { label: t('users.roleMember'), value: 'member' },
            { label: t('users.roleAdmin'), value: 'admin' },
            { label: t('users.roleSuperadmin'), value: 'superadmin' },
          ]}
          rules={[{ required: true }]}
        />
      </ModalForm>

      {/* Edit User Modal */}
      <ModalForm<UserUpdate>
        title={t('users.editUser', { username: currentUser?.username })}
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
        onFinish={handleUpdate}
        modalProps={{ destroyOnClose: true }}
        width={500}
        initialValues={currentUser || {}}
      >
        <ProFormText
          name="email"
          label={t('users.email')}
          placeholder={t('users.enterEmail')}
          rules={[{ type: 'email', message: t('users.emailInvalid') }]}
        />
        <ProFormText
          name="full_name"
          label={t('users.fullName')}
          placeholder={t('users.enterFullName')}
        />
        <ProFormSelect
          name="role"
          label={t('users.role')}
          options={[
            { label: t('users.roleMember'), value: 'member' },
            { label: t('users.roleAdmin'), value: 'admin' },
            { label: t('users.roleSuperadmin'), value: 'superadmin' },
          ]}
        />
      </ModalForm>
    </>
  )
}

export default Users
