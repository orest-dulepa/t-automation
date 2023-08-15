import { Organization } from '@/entities/Organization';

export interface IOrganizationUpdatePathParams {
  id: string;
}

export interface IOrganizationUpdateRequest extends Partial<Pick<Organization, 'name'>> {}

export interface IOrganizationUpdateResponse extends Pick<Organization, 'id' | 'name'> {}
