/**
 * Language Switcher Component
 *
 * Dropdown to switch between supported languages.
 */

import { Dropdown, Button } from 'antd'
import { GlobalOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { MenuProps } from 'antd'

const languages = [
  { key: 'en', label: 'English', flag: '🇺🇸' },
  { key: 'zh', label: '简体中文', flag: '🇨🇳' },
]

export function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const currentLang = languages.find((lang) => i18n.language.startsWith(lang.key)) || languages[0]

  const items: MenuProps['items'] = languages.map((lang) => ({
    key: lang.key,
    label: (
      <span>
        {lang.flag} {lang.label}
      </span>
    ),
    onClick: () => {
      i18n.changeLanguage(lang.key)
    },
  }))

  return (
    <Dropdown menu={{ items, selectedKeys: [currentLang.key] }} placement="bottomRight">
      <Button type="text" icon={<GlobalOutlined />}>
        {currentLang.flag} {currentLang.label}
      </Button>
    </Dropdown>
  )
}
