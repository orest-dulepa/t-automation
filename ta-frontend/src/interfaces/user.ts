import { IOrganization } from './organization';
import { IRole } from './role';

export interface IUser {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
  organization: IOrganization;
  role: IRole;
}
