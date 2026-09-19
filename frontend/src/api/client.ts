import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ClinicalData {
  subject_id: string
  age: number
  gender: number
  mmse?: number
  camcog?: number
  gds?: number
  fast?: number
  katz?: number
  barthel?: number
  lawton?: number
}

export interface PredictionRequest {
  clinical_data: ClinicalData
  run_segmentation: boolean
  run_shap: boolean
}

export interface JobStatus {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  message: string
  result?: PredictionResult
  error?: string
}

export interface PredictionResult {
  subject_id: string
  predicted_class: string
  predicted_label: number
  probabilities: Record<string, number>
  shap_explanation?: SHAPExplanation
  volumetric_features?: Record<string, number>
  segmentation_path?: string
}

export interface SHAPExplanation {
  subject_id: string
  predicted_class: string
  predicted_label: number
  probabilities: Record<string, number>
  top_features: Array<{
    feature: string
    shap_value: number
    feature_value: number
  }>
}

export interface Subject {
  subject_id: string
  age: number
  gender: number
  mmse?: number
  dxo_label?: number
}

export interface VolumetricData {
  volumes: Record<string, number>
  ratios: Record<string, number>
}

export interface ModelInfo {
  status: string
  model_path?: string
  feature_count?: number
  features?: string[]
  classes?: string[]
}

export interface FeatureImportance {
  feature: string
  mean_abs_shap: number
  Control_mean_abs_shap?: number
  BD_mean_abs_shap?: number
  DCL_mean_abs_shap?: number
  AD_mean_abs_shap?: number
  overall_mean_abs_shap?: number
}

export const predict = async (
  mriFile: File,
  clinicalData: ClinicalData,
  runSegmentation = true,
  runShap = false
): Promise<JobStatus> => {
  const formData = new FormData()
  formData.append('mri_file', mriFile)
  formData.append('clinical_data', JSON.stringify(clinicalData))
  formData.append('run_segmentation', String(runSegmentation))
  formData.append('run_shap', String(runShap))

  const response = await api.post<JobStatus>('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get<JobStatus>(`/jobs/${jobId}`)
  return response.data
}

export const listJobs = async (): Promise<JobStatus[]> => {
  const response = await api.get<JobStatus[]>('/jobs')
  return response.data
}

export const listSubjects = async (): Promise<Subject[]> => {
  const response = await api.get<Subject[]>('/subjects')
  return response.data
}

export const getSubject = async (subjectId: string): Promise<any> => {
  const response = await api.get(`/subjects/${subjectId}`)
  return response.data
}

export const getSubjectVolumes = async (subjectId: string): Promise<VolumetricData> => {
  const response = await api.get<VolumetricData>(`/subjects/${subjectId}/volumes`)
  return response.data
}

export const getSHAPExplanation = async (subjectId: string): Promise<SHAPExplanation> => {
  const response = await api.get<SHAPExplanation>(`/subjects/${subjectId}/shap`)
  return response.data
}

export const getModelInfo = async (): Promise<ModelInfo> => {
  const response = await api.get<ModelInfo>('/model/info')
  return response.data
}

export const getFeatureImportance = async (): Promise<FeatureImportance[]> => {
  const response = await api.get<FeatureImportance[]>('/model/feature-importance')
  return response.data
}

export const getSegmentationFile = (subjectId: string): string => {
  return `${API_BASE}/segmentation/${subjectId}`
}

export const getSHAPPlot = (subjectId: string, plotType: string): string => {
  return `${API_BASE}/shap/plots/${subjectId}/${plotType}`
}

export const healthCheck = async (): Promise<{ status: string; model_trained: boolean; data_available: boolean }> => {
  const response = await api.get('/health')
  return response.data
}

export default api