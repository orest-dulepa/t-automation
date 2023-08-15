import {
  Entity,
  PrimaryGeneratedColumn,
  PrimaryColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from 'typeorm';

import { IPropertyWithValue } from '@/@types/process';
import {AWS_PROCESS_STATUS_TO_STANDART_STATUS, PROCESS_STATUS} from '@/@types/users-processes';

import { User, RawUser } from './User';
import { Organization, RawOrganization } from './Organization';
import { Process, RawProcess } from './Process';

export interface RowUsersProcesses {
  id: number;
  status: PROCESS_STATUS;
  createTime: string;
  startTime: string | null;
  endTime: string | null;
  processRunId: string;
  duration: number | null;
  meta: IPropertyWithValue[];
  robocorpId: number | null;
  user?: RawUser;
  organization?: RawOrganization;
  process?: RawProcess;
}

@Entity({ name: 'users_processes' })
export class UsersProcesses {
  constructor(processRunId: string, user: User, organization: Organization, process: Process, meta: IPropertyWithValue[]) {
    this.processRunId = processRunId;
    this.user = user;
    this.createTime = new Date().toISOString();
    this.organization = organization;
    this.process = process;
    this.meta = meta;
  }

  static from = (rowUsersProcesses: RowUsersProcesses) => {
    const {
      id,
      status,
      createTime,
      startTime,
      endTime,
      processRunId,
      duration,
      meta,
      robocorpId,
      user: rawUser,
      organization: rawOrganization,
      process: rawProcess,
    } = rowUsersProcesses;

    const user = User.from(rawUser!);
    const organization = Organization.from(rawOrganization!);
    const process = Process.from(rawProcess!);

    const usersProcesses = new UsersProcesses(processRunId, user, organization, process, meta);

    usersProcesses.setId(id);
    usersProcesses.setStatus(status);
    usersProcesses.setCreateTime(createTime);
    usersProcesses.setStartTime(startTime);
    usersProcesses.setEndTime(endTime);
    usersProcesses.setDuration(duration);
    usersProcesses.setRobocorpRunId(robocorpId);

    return usersProcesses;
  };

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({
    name: 'status',
    type: 'enum',
    enum: PROCESS_STATUS,
    default: PROCESS_STATUS.INITIALIZED,
  })
  status: PROCESS_STATUS | AWS_PROCESS_STATUS_TO_STANDART_STATUS;

  @Column({ name: 'create_time', type: 'timestamp' })
  createTime: string;

  @Column({ name: 'start_time', type: 'timestamp' })
  startTime: string | null;

  @Column({ name: 'end_time', type: 'timestamp' })
  endTime: string | null;

  @Column({ name: 'robocorp_id', type: 'bigint' })
  robocorpId: number | null;

  @Column({ name: 'process_run_id', type: 'text' })
  processRunId: string;

  @Column({ name: 'duration', type: 'bigint' })
  duration: number | null;

  @Column({ name: 'meta', type: 'json' })
  meta: IPropertyWithValue[];

  @ManyToOne(() => User, (user) => user.id, { primary: true })
  @JoinColumn({ name: 'user_id', referencedColumnName: 'id' })
  user: User;

  @ManyToOne(() => Organization, (organization) => organization.id, { primary: true })
  @JoinColumn({ name: 'organization_id', referencedColumnName: 'id' })
  organization: Organization;

  @ManyToOne(() => Process, (process) => process.id, { primary: true })
  @JoinColumn({ name: 'process_id', referencedColumnName: 'id' })
  process: Process;

  public setId = (id: number) => {
    this.id = id;
  };

  public setStatus = (status: PROCESS_STATUS | AWS_PROCESS_STATUS_TO_STANDART_STATUS) => {
    this.status = status;
  };

  public setCreateTime = (createTime: string) => {
    this.createTime = createTime;
  };

  public setStartTime = (startTime: string | null) => {
    this.startTime = startTime;
  };

  public setEndTime = (endTime: string | null) => {
    this.endTime = endTime;
  };

  public setRobocorpRunId = (robocorpId: number | null) => {
    this.robocorpId = robocorpId;
  };

  public setProcessRunId = (processRunId: string) => {
    this.processRunId = processRunId;
  };

  public setDuration = (duration?: number | null) => {
    if (!duration && this.endTime && this.startTime) {
      const endTime = new Date(this.endTime);
      const startTime = new Date(this.startTime);

      this.duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
    } else if (duration) {
       this.duration = duration;
    }

    console.log('Duration', this.duration);
  };
}
