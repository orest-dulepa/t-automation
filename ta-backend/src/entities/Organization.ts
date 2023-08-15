import { Entity, PrimaryGeneratedColumn, PrimaryColumn, Column, OneToMany } from 'typeorm';
import { OrganizationsToProcesses } from './OrganizationsToProcesses';

export interface RawOrganization {
  id: number;
  name: string;
}

@Entity({ name: 'organizations' })
export class Organization {
  constructor(name: string) {
    this.name = name;
  }

  static from = (rawOrganization: RawOrganization) => {
    const { id, name } = rawOrganization;

    const organization = new Organization(name);

    organization.setId(id);

    return organization;
  };

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'name', type: 'text' })
  name: string;

  @OneToMany(() => OrganizationsToProcesses, (organizationsToProcesses) => organizationsToProcesses.organization)
  organizationToProcesses: OrganizationsToProcesses[];

  public setId = (id: number) => {
    this.id = id;
  };

  public setName = (name: string) => {
    this.name = name;
  };
}
