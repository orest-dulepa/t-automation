import { IPropertyWithValue } from '@/@types/process';

export type IProcessScheduleRequest = {
  timestamp: string,
  meta: IPropertyWithValue[],
};

export interface IProcessSchedulePathParams {
  id: string;
}

export interface IProcessScheduleResponse {};
