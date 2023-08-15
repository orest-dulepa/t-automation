import { Organization } from '@/entities/Organization';

export interface IOrganizationCreateRequest extends Pick<Organization, 'name'> {}

export interface IOrganizationCreateResponse extends Pick<Organization, 'id' | 'name'> {}
