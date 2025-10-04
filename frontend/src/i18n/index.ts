import { createI18n } from 'vue-i18n'
import { messages, type SupportedLocale } from './messages'

const defaultLocale = ((): SupportedLocale => {
  if (typeof window === 'undefined') {
    return 'zh-CN'
  }
  const stored = window.localStorage.getItem('promptworks-locale') as SupportedLocale | null
  return stored && stored in messages ? stored : 'zh-CN'
})()

export const i18n = createI18n({
  legacy: false,
  locale: defaultLocale,
  fallbackLocale: 'zh-CN',
  messages
})

export function setLocale(locale: SupportedLocale) {
  i18n.global.locale.value = locale
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('promptworks-locale', locale)
  }
}

export function getSupportedLocales() {
  return Object.keys(messages) as SupportedLocale[]
}
