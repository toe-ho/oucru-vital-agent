import client from "./api-client";
import type {
  AssessJobRequest,
  AssessJobResponse,
  AssessJobResultsResponse,
  AssessJobStatusResponse,
} from "@/types/api";

export async function triggerAssessment(req: AssessJobRequest): Promise<AssessJobResponse> {
  const res = await client.post<AssessJobResponse>("/assess", req);
  return res.data;
}

export async function getJobStatus(jobId: string): Promise<AssessJobStatusResponse> {
  const res = await client.get<AssessJobStatusResponse>(`/assessment-jobs/${jobId}`);
  return res.data;
}

export async function getJobResults(jobId: string): Promise<AssessJobResultsResponse> {
  const res = await client.get<AssessJobResultsResponse>(`/assessment-jobs/${jobId}/results`);
  return res.data;
}

export async function getJobLogs(
  jobId: string,
  params?: { stage?: string; tool?: string }
) {
  const res = await client.get(`/assessment-jobs/${jobId}/logs`, { params });
  return res.data;
}

export async function getSegmentDetail(jobId: string, segmentId: string) {
  const res = await client.get(`/assessment-jobs/${jobId}/segments/${segmentId}`);
  return res.data;
}
