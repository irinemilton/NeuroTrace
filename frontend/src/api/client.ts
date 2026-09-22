import axios from "axios";

/* ============================================================
   API CLIENT
============================================================ */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000,
});


/* ============================================================
   PROJECT STATUS
============================================================ */

export interface ProjectStatus {
  project: string;
  raw_mri_available: boolean;
  total_mri_subjects: number;
  segmented_subjects: number;
  segmentation_running: boolean;
  clinical_data_available: boolean;
  ml_dataset_available: boolean;
  model_available: boolean;
}


/* ============================================================
   SUBJECT
============================================================ */

export interface Subject {
  subject_id: string;
  mri_available: boolean;
  segmentation_available: boolean;
}


/* ============================================================
   SUBJECT DETAILS
============================================================ */

export interface SubjectDetails extends Subject {
  segmentation_path?: string | null;

  clinical_data?: Record<
    string,
    unknown
  > | null;

  imaging_features?: Record<
    string,
    unknown
  > | null;
}


/* ============================================================
   SEGMENTATION
============================================================ */

export interface SegmentationFile {
  subject_id: string;
  available: boolean;
  path: string;
  filename: string;
  size_bytes: number;
}


export interface SegmentationSubjectStatus {
  subject_id: string;
  mri_available: boolean;
  segmentation_available: boolean;
  segmentation_path?: string | null;
}


export interface SegmentationStatus {
  total: number;
  completed: number;
  remaining: number;
  subjects: SegmentationSubjectStatus[];
}


/* ============================================================
   MEASUREMENTS
============================================================ */

export interface MeasurementSide {
  voxel_count: number;

  voxel_spacing_mm: number[];

  voxel_volume_mm3: number;

  volume_mm3: number;

  dimensions_mm: number[];

  centroid_voxel: number[];

  centroid_mm: number[];

  bounding_box_voxels: number[];

  connected_components: number;
}


export interface BilateralMeasurement {
  left: MeasurementSide;
  right: MeasurementSide;

  total_volume_mm3: number;

  asymmetry_percent: number;
}


export interface SubjectMeasurements {
  segmentation_file: string;

  image_shape: number[];

  voxel_spacing_mm: number[];

  voxel_volume_mm3: number;

  regions: Record<
    string,
    BilateralMeasurement
  >;
}


export interface SubjectMeasurementsResponse {
  subject_id: string;

  status: string;

  measurements: SubjectMeasurements;
}


/* ============================================================
   ALZHEIMER ML
============================================================ */

export interface AlzheimerPrediction {
  prediction: number;

  classification: "AD" | "Non-AD" | string;

  probability_ad: number;

  probability_non_ad: number;

  model: string;

  model_C: number;

  features_used: number;
}


export interface AnalysisResult {
  status: string;

  subject_id: string;

  segmentation_available: boolean;

  prediction_available: boolean;

  prediction?: AlzheimerPrediction | null;

  message: string;
}


/* ============================================================
   MODEL EXPLANATION
============================================================ */

export interface ExplanationFeature {
  feature: string;

  contribution: number;

  direction: "AD" | "Non-AD";
}


export interface ExplanationResult {
  features: ExplanationFeature[];
}


/* ============================================================
   HEALTH
============================================================ */

export interface HealthStatus {
  status: string;

  service: string;

  version: string;
}


/* ============================================================
   PROJECT STATUS
============================================================ */

export async function getProjectStatus(): Promise<ProjectStatus> {
  const response =
    await api.get<ProjectStatus>("/status");

  return response.data;
}


/* ============================================================
   SUBJECTS
============================================================ */

export async function listSubjects(): Promise<Subject[]> {
  const response =
    await api.get<{
      count: number;
      subjects: Subject[];
    }>("/subjects");

  return response.data.subjects;
}


/* ============================================================
   SUBJECT DETAILS
============================================================ */

export async function getSubject(
  subjectId: string,
): Promise<SubjectDetails> {
  const response =
    await api.get<SubjectDetails>(
      `/subjects/${encodeURIComponent(subjectId)}`,
    );

  return response.data;
}


/* ============================================================
   SEGMENTATION STATUS
============================================================ */

export async function getSegmentationStatus(): Promise<SegmentationStatus> {
  const response =
    await api.get<SegmentationStatus>(
      "/segmentation/status",
    );

  return response.data;
}


/* ============================================================
   SEGMENTATION FILE
============================================================ */

export async function getSegmentation(
  subjectId: string,
): Promise<SegmentationFile> {
  const response =
    await api.get<SegmentationFile>(
      `/subjects/${encodeURIComponent(subjectId)}/segmentation`,
    );

  return response.data;
}


/* ============================================================
   MEASUREMENTS
============================================================ */

export async function getSubjectMeasurements(
  subjectId: string,
): Promise<SubjectMeasurementsResponse> {
  const response =
    await api.get<SubjectMeasurementsResponse>(
      `/subjects/${encodeURIComponent(subjectId)}/measurements`,
    );

  return response.data;
}


/* ============================================================
   RUN ALZHEIMER ANALYSIS
============================================================ */

export async function analyzeSubject(
  subjectId: string,
): Promise<AnalysisResult> {
  const response =
    await api.post<AnalysisResult>(
      "/analyze",
      {
        subject_id: subjectId,
      },
    );

  return response.data;
}


/* ============================================================
   MODEL EXPLANATION
============================================================ */

export async function getSubjectExplanation(
  subjectId: string,
): Promise<ExplanationResult> {
  const response =
    await api.get<ExplanationResult>(
      `/subjects/${encodeURIComponent(subjectId)}/explanation`,
    );

  return response.data;
}


/* ============================================================
   HEALTH CHECK
============================================================ */

export async function healthCheck(): Promise<HealthStatus> {
  const response =
    await api.get<HealthStatus>(
      "/../health",
    );

  return response.data;
}


/* ============================================================
   DEFAULT EXPORT
============================================================ */

export default api;