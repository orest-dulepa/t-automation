import { UsersProcesses } from '@/entities/UsersProcesses';

export interface IUsersProcessesGetPathParams {
  id: string;
}

export interface IUsersProcessesGetResponse extends UsersProcesses {
  artifacts?: Array<{ key?: string; size?: number }>;
  logs: string;
  events: Array<{ seqNo: string; eventType: string; timeStamp: string }>;
}
