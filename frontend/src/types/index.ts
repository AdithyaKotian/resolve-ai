export interface BackendHealth {
  status: "ok";
  app_name: string;
  version: string;
  environment: string;
  database: "connected";
  timestamp: string;
}