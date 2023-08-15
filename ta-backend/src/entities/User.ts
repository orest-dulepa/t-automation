import {
  Entity,
  PrimaryGeneratedColumn,
  PrimaryColumn,
  Column,
  OneToMany,
  OneToOne,
  JoinColumn,
} from 'typeorm';
import { Organization, RawOrganization } from './Organization';
import { UsersProcesses } from './UsersProcesses';
import { Role } from './Role';

export interface RawUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  otp: string | null;
  organization?: RawOrganization;
}

@Entity({ name: 'users' })
export class User {
  constructor(email: string, firstName: string, lastName: string, organization: Organization) {
    this.email = email;
    this.firstName = firstName;
    this.lastName = lastName;
    this.organization = organization;
  }

  static from = (rawUser: RawUser) => {
    const { id, email, firstName, lastName, organization: rawOrganization } = rawUser;

    const organization = Organization.from(rawOrganization!);

    const user = new User(email, firstName, lastName, organization);

    user.setId(id);

    return user;
  };

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'email', type: 'text', unique: true })
  email: string;

  @Column({ name: 'first_name', type: 'text' })
  firstName: string;

  @Column({ name: 'last_name', type: 'text' })
  lastName: string;

  @Column({ name: 'otp', type: 'text', nullable: true })
  otp: string | null;

  @OneToOne(() => Organization, (organization) => organization.id)
  @JoinColumn({ name: 'organization_id', referencedColumnName: 'id' })
  organization: Organization;

  @OneToOne(() => Role, (role) => role.id)
  @JoinColumn({ name: 'role_id', referencedColumnName: 'id' })
  role: Role;

  @OneToMany(() => UsersProcesses, (usersProcesses) => usersProcesses.user)
  usersProcesses: UsersProcesses[];

  public setId = (id: number) => {
    this.id = id;
  };

  public setEmail = (email: string) => {
    this.email = email;
  };

  public setFirstName = (firstName: string) => {
    this.firstName = firstName;
  };

  public setLastName = (lastName: string) => {
    this.lastName = lastName;
  };

  public setOtp = (otp: string | null) => {
    this.otp = otp;
  };
}
