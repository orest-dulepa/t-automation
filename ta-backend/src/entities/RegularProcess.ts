import {
  Entity,
  PrimaryGeneratedColumn,
  PrimaryColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { IPropertyWithValue } from '@/@types/process';
import { User } from './User';
import { Process } from './Process';
import { Organization } from './Organization';
import {DAY_OF_WEEK} from "@/@types/day-of-week";


@Entity({ name: 'regular_processes' })
export class RegularProcess {
  constructor(
    daysOfWeek: string[],
    startTime: string,
    meta: IPropertyWithValue[],
    user: User,
    process: Process,
    organization: Organization,
  ) {
    let sortedDaysOfWeek: string[] = [];

    if (Array.isArray(daysOfWeek)) {
      for (let dayOfWeek in DAY_OF_WEEK) {
        if (daysOfWeek.includes(dayOfWeek)) {
          sortedDaysOfWeek.push(dayOfWeek);
        }
      }
    }

    this.daysOfWeek = sortedDaysOfWeek;
    this.startTime = startTime;
    this.meta = meta;
    this.user = user;
    this.process = process;
    this.organization = organization;
  }

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'days_of_week', type: 'json' })
  daysOfWeek: string[];

  @Column({ name: 'start_time', type: 'time' })
  startTime: string;

  @Column({ name: 'meta', type: 'json' })
  meta: IPropertyWithValue[];

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
