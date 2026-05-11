import client from "./api-client";
import type { DashboardSummaryResponse, TimelineResponse } from "@/types/api";

export async function getDashboardSummary(
  params?: { days?: number; signal_type?: string }
): Promise<DashboardSummaryResponse> {
  const res = await client.get<DashboardSummaryResponse>("/dashboard/summary", { params });
  return res.data;
}

export async function getTimeline(jobId: string): Promise<TimelineResponse> {
  const res = await client.get<TimelineResponse>(`/dashboard/timeline/${jobId}`);
  return res.data;
}
