import { Entity, PrimaryGeneratedColumn, PrimaryColumn, Column } from 'typeorm';
import {PROCESS_TYPE, IRobocorpCredential, IProperty, IAWSBotCredential} from '@/@types/process';

export interface RawProcess {
  id: number;
  name: string;
  type: PROCESS_TYPE;
  credentials: IRobocorpCredential | IAWSBotCredential;
  // credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential;
  properties: IProperty[];
}

@Entity({ name: 'processes' })
export class Process {
  constructor(
    name: string,
    type: PROCESS_TYPE,
    credentials: IRobocorpCredential | IAWSBotCredential,
    // credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential,
    properties: IProperty[] = [],
  ) {
    this.name = name;
    this.type = type;
    this.credentials = credentials;
    this.properties = properties;
  }

  static from = (rawProcess: RawProcess) => {
    const { id, name, type, credentials, properties } = rawProcess;

    const process = new Process(name, type, credentials, properties);

    process.setId(id);

    return process;
  };

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'name', type: 'text' })
  name: string;

  @Column({
    name: 'type',
    type: 'enum',
    enum: PROCESS_TYPE,
  })
  type: PROCESS_TYPE;

  @Column({ name: 'credentials', type: 'json' })
  credentials: IRobocorpCredential | IAWSBotCredential;
  // credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential;

  @Column({ name: 'properties', type: 'json' })
  properties: IProperty[];

  public setId = (id: number) => {
    this.id = id;
  };

  public setName = (name: string) => {
    this.name = name;
  };

  public setType = (type: PROCESS_TYPE) => {
    this.type = type;
  };

  // public setCredentials = (credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential) => {
  //   this.credentials = credentials;
  // };

  public setProperties = (properties: IProperty[]) => {
    this.properties = properties;
  };
}
