import { DaysOfWeek } from '@/@types/days-of-week';
import { IOrganization } from './organization';
import { IProcess, IPropertyWithValue } from './process';
import { IUser } from './user';

export interface IRegularProcess {
  id: number;
  daysOfWeek: DaysOfWeek[];
  startTime: string;
  meta: IPropertyWithValue[];
  organization: IOrganization;
  process: IProcess;
  user: IUser;
}
