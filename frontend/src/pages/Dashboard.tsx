import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Brain, FileText, Users, TrendingUp, Clock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { api, Subject, ModelInfo, JobStatus } from '../api/client'
import { cn, formatNumber, getDiagnosisLabel, getDiagnosisColor } from '../utils/helpers'

export function Dashboard() {
  const [subjects, setSubjects] = useState<Subject[]>([])
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null)
  const [recentJobs, setRecentJobs] = useState<JobStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [subjectsData, modelData, jobsData] = await Promise.all([
        api.listSubjects(),
        api.getModelInfo(),
        api.listJobs(),
      ])
      setSubjects(subjectsData)
      setModelInfo(modelData)
      setRecentJobs(jobsData.slice(0, 5))
    } catch (err) {
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const stats = [
    { label: 'Total Subjects', value: subjects.length, icon: Users, color: 'text-blue-600 bg-blue-100' },
    { label: 'Model Status', value: modelInfo?.status === 'trained' ? 'Trained' : 'Not Trained', icon: Brain, color: modelInfo?.status === 'trained' ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100' },
    { label: 'Features', value: modelInfo?.feature_count || 0, icon: FileText, color: 'text-purple-600 bg-purple-100' },
    { label: 'Recent Jobs', value: recentJobs.length, icon: Clock, color: 'text-orange-600 bg-orange-100' },
  ]

  const classDistribution = subjects.reduce((acc, s) => {
    const label = s.dxo_label !== undefined ? getDiagnosisLabel(s.dxo_label) : 'Unknown'
    acc[label] = (acc[label] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-neuro-900 mb-2">Failed to load data</h3>
          <p className="text-neuro-500 mb-4">{error}</p>
          <button onClick={loadData} className="btn-primary">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neuro-900">Dashboard</h1>
          <p className="text-neuro-500 mt-1">Overview of your neuroimaging analysis pipeline</p>
        </div>
        <Link to="/analyze" className="btn-primary">
          <FileText className="w-4 h-4 mr-2" />
          New Analysis
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="card">
            <div className="card-body">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neuro-500">{stat.label}</p>
                  <p className="text-2xl font-bold text-neuro-900 mt-1">{stat.value}</p>
                </div>
                <div className={cn('p-3 rounded-xl', stat.color)}>
                  <stat.icon className="w-6 h-6" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-neuro-900">Class Distribution</h2>
          </div>
          <div className="card-body">
            {Object.keys(classDistribution).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(classDistribution).map(([label, count]) => (
                  <div key={label} className="flex items-center gap-4">
                    <span className={cn('px-2 py-1 rounded text-xs font-medium w-20 text-center', getDiagnosisColor(label))}>
                      {label}
                    </span>
                    <div className="flex-1 h-4 bg-neuro-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-600 rounded-full transition-all duration-500"
                        style={{ width: `${(count / subjects.length) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-neuro-700 w-12 text-right">{count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neuro-500 text-center py-8">No subject data available</p>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-lg font-semibold text-neuro-900">Recent Analyses</h2>
            <Link to="/subjects" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="card-body">
            {recentJobs.length > 0 ? (
              <div className="space-y-3">
                {recentJobs.map((job) => (
                  <div key={job.job_id} className="flex items-center justify-between p-3 bg-neuro-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={cn('w-2 h-2 rounded-full', {
                        'bg-green-500': job.status === 'completed',
                        'bg-yellow-500 animate-pulse': job.status === 'running',
                        'bg-red-500': job.status === 'failed',
                        'bg-neuro-400': job.status === 'queued',
                      })} />
                      <div>
                        <p className="text-sm font-medium text-neuro-900">Job {job.job_id.slice(0, 8)}</p>
                        <p className="text-xs text-neuro-500">{job.message}</p>
                      </div>
                    </div>
                    <span className={cn('text-xs px-2 py-1 rounded-full', {
                      'bg-green-100 text-green-700': job.status === 'completed',
                      'bg-yellow-100 text-yellow-700': job.status === 'running',
                      'bg-red-100 text-red-700': job.status === 'failed',
                      'bg-neuro-100 text-neuro-700': job.status === 'queued',
                    })}>
                      {job.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-neuro-500 text-center py-8">No recent analyses</p>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-neuro-900">Quick Actions</h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/analyze" className="card p-6 hover:border-primary-300 transition-colors text-center">
              <Brain className="w-12 h-12 text-primary-600 mx-auto mb-3" />
              <h3 className="font-medium text-neuro-900">Run New Analysis</h3>
              <p className="text-sm text-neuro-500 mt-1">Upload MRI and clinical data for prediction</p>
            </Link>
            <Link to="/subjects" className="card p-6 hover:border-primary-300 transition-colors text-center">
              <Users className="w-12 h-12 text-primary-600 mx-auto mb-3" />
              <h3 className="font-medium text-neuro-900">Browse Subjects</h3>
              <p className="text-sm text-neuro-500 mt-1">View all subjects and their results</p>
            </Link>
            <Link to="/model" className="card p-6 hover:border-primary-300 transition-colors text-center">
              <TrendingUp className="w-12 h-12 text-primary-600 mx-auto mb-3" />
              <h3 className="font-medium text-neuro-900">Model Insights</h3>
              <p className="text-sm text-neuro-500 mt-1">Feature importance and model performance</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}