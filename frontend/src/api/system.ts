/**
 * 系统信息相关 API
 */

import { request } from './request'

export interface VersionInfo {
  version: string
  version_info: [number, number, number]
  history: Record<string, string>
}

export interface HealthInfo {
  status: string
  version: string
  message: string
}

/**
 * 获取系统版本信息
 */
export const getSystemVersion = (): Promise<VersionInfo> => {
  return request.get('/system/version')
}

/**
 * 系统健康检查
 */
export const getSystemHealth = (): Promise<HealthInfo> => {
  return request.get('/system/health')
}