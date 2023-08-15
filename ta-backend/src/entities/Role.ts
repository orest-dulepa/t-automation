import { Entity, PrimaryGeneratedColumn, PrimaryColumn, Column } from 'typeorm';

@Entity({ name: 'roles' })
export class Role {
  constructor(name: string) {
    this.name = name;
  }

  @PrimaryGeneratedColumn()
  @PrimaryColumn({ name: 'id', type: 'bigint' })
  id: number;

  @Column({ name: 'name', type: 'text' })
  name: string;
}
