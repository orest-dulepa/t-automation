import {
    Entity,
    PrimaryGeneratedColumn,
    PrimaryColumn,
    Column,
    OneToOne,
    JoinColumn,
  } from 'typeorm';
  import { UsersProcesses } from './UsersProcesses';
  
  @Entity({ name: 'logs' })
  export class Log {
    constructor(text: string, userProcess: UsersProcesses) {
      this.text = text;
      this.userProcess = userProcess;
    }
  
    @PrimaryGeneratedColumn()
    @PrimaryColumn({ name: 'id', type: 'bigint' })
    id: number;
  
    @Column({ name: 'text', type: 'text' })
    text: string;
  
    @OneToOne(() => UsersProcesses, (usersProcesses) => usersProcesses.id)
    @JoinColumn({ name: 'user_process_id', referencedColumnName: 'id' })
    userProcess: UsersProcesses;
  }
