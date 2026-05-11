import client from "./api-client";
import type { ReportGenerateRequest, ReportResponse } from "@/types/api";

export async function generateReport(req: ReportGenerateRequest): Promise<{ report_id: string; status: string }> {
  const res = await client.post("/reports/generate", req);
  return res.data;
}

export async function getReport(reportId: string, format?: "json" | "html" | "pdf"): Promise<ReportResponse> {
  const res = await client.get<ReportResponse>(`/reports/${reportId}`, {
    params: format ? { format } : undefined,
  });
  return res.data;
}

export async function downloadReportPdf(reportId: string, filename: string): Promise<void> {
  const res = await client.get(`/reports/${reportId}`, {
    params: { format: "pdf" },
    responseType: "blob",
  });
  const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
