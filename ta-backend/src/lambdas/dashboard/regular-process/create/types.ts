import { DAY_OF_WEEK } from '@/@types/day-of-week';
import { IPropertyWithValue } from '@/@types/process';


export interface ICreateRegularProcessRequest {
  processId: number;
  meta: IPropertyWithValue[];
  daysOfWeek: DAY_OF_WEEK[];
  startTime: string;
}

export interface ICreateRegularProcessResponse {}
