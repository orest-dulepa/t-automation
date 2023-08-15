import { IProcess, IPropertyWithValue } from '@/interfaces/process';
import { IUserProcess, IUserProcessDetails } from '@/interfaces/user-process';
import { IQueries } from '@/interfaces/filter';
import { IUser } from '@/interfaces/user';
import { IScheduledProcess } from '@/interfaces/scheduled-process';
import { DaysOfWeek } from '@/@types/days-of-week';
import {IRegularProcess} from "@/interfaces/regular-process";

export interface IGetMeResponse extends IUser {}

export type IGetAvailableProcessResponse = IProcess[];

export type IScheduleProcessBody = {
  timestamp: string;
  meta: IPropertyWithValue[],
};

export type IGetScheduledProcessesResponse = IScheduledProcess[];

export type IGetRegularProcessesResponse = IRegularProcess[];

export type IStartProcessBody = IPropertyWithValue[];

export interface IStartProcessResponse extends IUserProcess {}

export type IGetActiveProcessesResponse = IUserProcess[];

export interface IGetFinishedProcessesQueries extends IQueries {}

export interface IGetFinishedProcessesResponse {
  processes: IUserProcess[],
  total: number,
}

export interface IGetFinishedProcessesFiltersResponse {
  processes: IProcess[],
  users: IUser[],
}

export interface IGetUserProcessResponse extends IUserProcessDetails {}

export interface IDownloadUrlBody {
  key: string;
}

export interface IDownloadUrlResponse {
  url: string;
}

export type IEmptyResponse = {};

export interface ICreateRegularProcessRequest {
  processId: number;
  meta: IPropertyWithValue[];
  daysOfWeek: DaysOfWeek[];
  startTime: string;
}
