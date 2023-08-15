import { Entity, ManyToOne, JoinColumn } from 'typeorm';
import { Organization, RawOrganization } from './Organization';
import { Process, RawProcess } from './Process';

export interface RawOrganizationsToProcesses {
  organization?: RawOrganization;
  process?: RawProcess;
}

@Entity({ name: 'organizations_to_processes' })
export class OrganizationsToProcesses {
  constructor(organization: Organization, process: Process) {
    this.organization = organization;
    this.process = process;
  }

  @ManyToOne(() => Organization, (organization) => organization.id, { primary: true })
  @JoinColumn({ name: 'organization_id', referencedColumnName: 'id' })
  organization: Organization;

  @ManyToOne(() => Process, (process) => process.id, { primary: true })
  @JoinColumn({ name: 'process_id', referencedColumnName: 'id' })
  process: Process;
}
