import client from "./api-client";
import type {
  RecordingDetailResponse,
  RecordingListResponse,
  UploadResponse,
  WaveformResponse,
} from "@/types/api";

export async function uploadRecording(
  file: File,
  signalType: string,
  samplingRate: number,
  opts?: { subjectId?: string; deviceId?: string; notes?: string }
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("signal_type", signalType);
  form.append("sampling_rate", String(samplingRate));
  if (opts?.subjectId) form.append("subject_id", opts.subjectId);
  if (opts?.deviceId) form.append("device_id", opts.deviceId);
  if (opts?.notes) form.append("notes", opts.notes);

  const res = await client.post<UploadResponse>("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function listRecordings(
  params?: { signal_type?: string; status?: string; limit?: number; offset?: number }
): Promise<RecordingListResponse> {
  const res = await client.get<RecordingListResponse>("/recordings", { params });
  return res.data;
}

export async function getRecording(id: string): Promise<RecordingDetailResponse> {
  const res = await client.get<RecordingDetailResponse>(`/recordings/${id}`);
  return res.data;
}

export async function getWaveform(
  id: string,
  params?: { start?: number; end?: number; downsample?: number }
): Promise<WaveformResponse> {
  const res = await client.get<WaveformResponse>(`/recordings/${id}/waveform`, { params });
  return res.data;
}
