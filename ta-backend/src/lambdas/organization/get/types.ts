import { Organization } from '@/entities/Organization';

export interface IOrganizationGetPathParams {
  id: string;
}

export interface IOrganizationGetResponse extends Pick<Organization, 'id' | 'name'> {}
