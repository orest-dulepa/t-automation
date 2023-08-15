import { IProcess, IPropertyWithValue } from './process';
import { IUser } from './user';

export enum ProcessStatus {
  ACTIVE = 'active',
  PROCESSING = 'processing',
  FINISHED = 'finished',
  FAILED = 'failed',
  WARNING = 'warning',
  INITIALIZED = 'initialized',
  SCHEDULED = 'scheduled',
  REGULAR = 'regular'
}

export interface IUserProcess {
  id: number;
  createTime: string;
  status: ProcessStatus;
  startTime: string;
  endTime: null | string;
  duration: null | number;
  processRunId: string;
  process: IProcess;
  meta: IPropertyWithValue[];
  user: IUser;
  robocorpId: null | number;
}

export interface IUserProcessDetails extends IUserProcess {
  artifacts?: Array<{ key?: string; size?: number }>;
  logs: string;
  events: Array<{ seqNo: string; eventType: string; timeStamp: string }>;
}
