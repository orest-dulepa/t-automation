import { IRobocorpCredential } from '@/@types/process';

export interface IStartRobotResponse {
  message: string;
  processRunId: string;
  processId: string;
  workspaceId: string;
  workItemId: string;
}

export interface IStartRobotV2Response {
  id: string;
}

export interface IMonitorRobotArguments extends IRobocorpCredential {
  processRunId: string;
}

export interface IMonitorRobotResponse {
  id: string;
  runNo: number;
  result: string;
  state: string;
  errorCode: string;
  duration: number;
  workspaceId: string;
  workItemStats: {
    totalCount: number;
    failedCount: number;
    succeededCount: number;
  };
  robotRuns: Array<{ id: string }>;
}

export interface IRobotArtifactsArguments extends IMonitorRobotArguments {
  robotRunsId: string;
}

export interface IRobotArtifactsResponse {
  id: string;
  fileName: string;
  fileSize: number;
}

export interface IRobotDownloadArtifactArguments extends IRobotArtifactsArguments {
  artifactId: string;
  fileName: string;
}

export interface IDownloadArtifactArguments {
  link: string;
}

export interface IRobotDownloadEventsArguments extends IRobotArtifactsArguments {}

export type IRobotDownloadEventsResponse = Array<{
  seqNo: string;
  data?: {
    [key: string]: any;
  };
  timeStamp: string;
  eventType: string;
}>;

export interface IRobotDownloadLogsArguments extends IRobotArtifactsArguments {};

export type IRobotDownloadLogsResponse = Array<{
  seqNo: number;
  message: string;
}>;
