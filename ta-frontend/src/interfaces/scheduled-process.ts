import { IOrganization } from './organization';
import { IProcess, IPropertyWithValue } from './process';
import { IUser } from './user';
import { ProcessStatus } from './user-process';

export interface IScheduledProcess {
  id: number;
  meta: IPropertyWithValue[];
  organization: IOrganization;
  process: IProcess;
  startTime: string;
  status: ProcessStatus;
  user: IUser;
}
