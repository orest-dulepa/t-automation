import {
  Entity,
  PrimaryGeneratedColumn,
  PrimaryColumn,
  Column,
  OneToOne,
  JoinColumn,
} from 'typeorm';
import { UsersProcesses } from './UsersProcesses';

@Entity({ name: 'events' })
export class Event {
  constructor(seqNo: string, timeStamp: string, eventType: string, userProcess: UsersProcesses) {
    this.seqNo = seqNo;
    this.timeStamp = timeStamp;
    this.eventType = eventType;
    this.userProcess = userProcess;
  }

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'seq_no', type: 'text' })
  seqNo: string;

  @Column({ name: 'time', type: 'text' })
  timeStamp: string;

  @Column({ name: 'event_type', type: 'text' })
  eventType: string;

  @OneToOne(() => UsersProcesses, (usersProcesses) => usersProcesses.id)
  @JoinColumn({ name: 'user_process_id', referencedColumnName: 'id' })
  userProcess: UsersProcesses;
}
