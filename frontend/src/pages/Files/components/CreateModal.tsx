import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Modal, Form, Input, message } from 'antd'
import { createFileOrDirectoryApiV1FilesCreatePost } from '../../../api/client'

interface CreateModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
  isDirectory: boolean
  currentPath: string
}

const CreateModal: React.FC<CreateModalProps> = ({
  open,
  onClose,
  onSuccess,
  isDirectory,
  currentPath,
}) => {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      const { error } = await createFileOrDirectoryApiV1FilesCreatePost({
        body: {
          path: currentPath,
          name: values.name,
          is_directory: isDirectory,
          content: isDirectory ? undefined : values.content || '',
        },
      })

      if (error) {
        message.error(t('files.createFailed'))
        return
      }

      message.success(
        isDirectory ? t('files.folderCreated') : t('files.fileCreated')
      )
      form.resetFields()
      onSuccess()
    } catch {
      // Validation error, ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isDirectory ? t('files.newFolder') : t('files.newFile')}
      open={open}
      onOk={handleSubmit}
      onCancel={() => {
        form.resetFields()
        onClose()
      }}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label={t('files.name')}
          rules={[
            { required: true, message: t('files.nameRequired') },
            {
              pattern: /^[^/\\:*?"<>|]+$/,
              message: t('files.invalidName'),
            },
          ]}
        >
          <Input
            placeholder={
              isDirectory
                ? t('files.enterFolderName')
                : t('files.enterFileName')
            }
            autoFocus
          />
        </Form.Item>

        {!isDirectory && (
          <Form.Item name="content" label={t('files.content')}>
            <Input.TextArea
              rows={6}
              placeholder={t('files.enterContent')}
            />
          </Form.Item>
        )}
      </Form>
    </Modal>
  )
}

export default CreateModal
