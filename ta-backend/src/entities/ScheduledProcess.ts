import {
  Entity,
  PrimaryGeneratedColumn,
  PrimaryColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from 'typeorm';

import { IPropertyWithValue } from '@/@types/process';
import { SCHEDULED_PROCESS_STATUS } from '@/@types/scheduled-processes';

import { User } from './User';
import { Process } from './Process';
import { Organization } from './Organization';

@Entity({ name: 'scheduled_processes' })
export class ScheduledProcess {
  constructor(
    meta: IPropertyWithValue[],
    startTime: number,
    user: User,
    process: Process,
    organization: Organization,
  ) {
    this.meta = meta;
    this.startTime = startTime;
    this.user = user;
    this.process = process;
    this.organization = organization;
  }

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({
    name: 'status',
    type: 'enum',
    enum: SCHEDULED_PROCESS_STATUS,
    default: SCHEDULED_PROCESS_STATUS.SCHEDULED,
  })
  status: SCHEDULED_PROCESS_STATUS;

  @Column({ name: 'meta', type: 'json' })
  meta: IPropertyWithValue[];

  @Column({ name: 'start_time', type: 'bigint' })
  startTime: number;

  @ManyToOne(() => User, (user) => user.id, { primary: true })
  @JoinColumn({ name: 'user_id', referencedColumnName: 'id' })
  user: User;

  @ManyToOne(() => Process, (process) => process.id, { primary: true })
  @JoinColumn({ name: 'process_id', referencedColumnName: 'id' })
  process: Process;

  @ManyToOne(() => Organization, (organization) => organization.id, { primary: true })
  @JoinColumn({ name: 'organization_id', referencedColumnName: 'id' })
  organization: Organization;
}
