import { AbstractRepository, EntityRepository } from 'typeorm';
import { Process } from '@/entities/Process';

@EntityRepository(Process)
export class ProcessRepository extends AbstractRepository<Process> {
  public insert = (process: Process) => this.repository.save(process);

  public getAll = () =>
    this.repository
      .createQueryBuilder()
      .getMany();

  public getById = (id: number | string) =>
    this.repository
      .createQueryBuilder()
      .where('id = :id', { id })
      .getOne();

  public update = (process: Process) => this.repository.save(process);

  public delete = (id: string) =>
    this.repository
      .createQueryBuilder()
      .delete()
      .where('id = :id', { id })
      .execute();
}
