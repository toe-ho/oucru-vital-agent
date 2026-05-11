import axios, { AxiosError } from "axios";

export class APIError extends Error {
  constructor(
    public error: string,
    public detail: string,
    public status: number
  ) {
    super(detail);
    this.name = "APIError";
  }
}

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api",
  timeout: 60000,
});

client.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ error: string; detail: string }>) => {
    const data = err.response?.data;
    throw new APIError(
      data?.error ?? "UnknownError",
      data?.detail ?? err.message,
      err.response?.status ?? 0
    );
  }
);

export default client;
