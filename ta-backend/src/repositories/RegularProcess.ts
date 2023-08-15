import { AbstractRepository, EntityRepository } from 'typeorm';
import { RegularProcess } from '@/entities/RegularProcess';

@EntityRepository(RegularProcess)
export class RegularProcessRepository extends AbstractRepository<RegularProcess> {
  public insert = (regularProcess: RegularProcess) => this.repository.save(regularProcess);
  public update = (regularProcess: RegularProcess) => this.repository.save(regularProcess);

  public getById = (id: number) =>
    this.repository
      .createQueryBuilder()
      .where('id = :id', { id })
      .getOne();

  public getAllRegular = (organizationId?: number, userId?: number) => {
    const query = this.repository
      .createQueryBuilder('regularProcesses')
      .leftJoinAndSelect('regularProcesses.process', 'processes')
      .leftJoinAndSelect('regularProcesses.user', 'users')
      .leftJoinAndSelect('regularProcesses.organization', 'organizations');

    if (organizationId) {
      query.andWhere('regularProcesses.organization.id = :id', { id: organizationId });
    }

    if (userId) {
      query.andWhere('regularProcesses.user.id = :id', { id: userId });
    }

    return query.getMany();
  };

  public delete = (id: string) =>
    this.repository
      .createQueryBuilder()
      .delete()
      .where('id = :id', { id })
      .execute();
}
