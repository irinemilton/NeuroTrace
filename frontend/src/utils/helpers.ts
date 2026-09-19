import { clsx, type ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatNumber(num: number | undefined | null, decimals = 1): string {
  if (num === undefined || num === null) return 'N/A'
  return num.toFixed(decimals)
}

export function formatPercent(num: number | undefined | null): string {
  if (num === undefined || num === null) return 'N/A'
  return `${(num * 100).toFixed(1)}%`
}

export function getDiagnosisColor(label: number | string): string {
  const colors: Record<string, string> = {
    0: 'bg-green-100 text-green-800',
    1: 'bg-blue-100 text-blue-800',
    2: 'bg-yellow-100 text-yellow-800',
    3: 'bg-red-100 text-red-800',
    Control: 'bg-green-100 text-green-800',
    BD: 'bg-blue-100 text-blue-800',
    DCL: 'bg-yellow-100 text-yellow-800',
    AD: 'bg-red-100 text-red-800',
  }
  return colors[String(label)] || 'bg-neuro-100 text-neuro-800'
}

export function getDiagnosisLabel(label: number | string): string {
  const labels: Record<string, string> = {
    0: 'Control',
    1: 'BD',
    2: 'DCL',
    3: 'AD',
  }
  return labels[String(label)] || String(label)
}

export function getGenderLabel(gender: number | string): string {
  return String(gender) === '1' ? 'Female' : 'Male'
}

export function truncateFeatureName(name: string, maxLength = 30): string {
  if (name.length <= maxLength) return name
  return name.substring(0, maxLength - 3) + '...'
}

export function groupVolumesByRegion(volumes: Record<string, number>): Record<string, number[]> {
  const groups: Record<string, number[]> = {}
  Object.entries(volumes).forEach(([key, value]) => {
    const region = key.replace('vol_', '').replace(/_left|_right$/i, '').replace(/_ratio$/, '')
    if (!groups[region]) groups[region] = []
    groups[region].push(value)
  })
  return groups
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function pollJob(
  getStatus: (jobId: string) => Promise<any>,
  jobId: string,
  onUpdate: (status: any) => void,
  interval = 2000
): Promise<any> {
  return new Promise((resolve, reject) => {
    const check = async () => {
      try {
        const status = await getStatus(jobId)
        onUpdate(status)
        if (status.status === 'completed') {
          resolve(status.result)
        } else if (status.status === 'failed') {
          reject(new Error(status.error || 'Job failed'))
        } else {
          setTimeout(check, interval)
        }
      } catch (err) {
        reject(err)
      }
    }
    check()
  })
}