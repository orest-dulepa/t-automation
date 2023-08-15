import { AbstractRepository, EntityRepository } from 'typeorm';
import { OrganizationsToProcesses } from '@/entities/OrganizationsToProcesses';

@EntityRepository(OrganizationsToProcesses)
export class OrganizationsToProcessesRepository extends AbstractRepository<OrganizationsToProcesses> {
  public insert = (organizationsToProcesses: OrganizationsToProcesses) =>
    this.repository.save(organizationsToProcesses);

  public getByOrganizationId = (id: number) =>
    this.repository
      .createQueryBuilder('organizationsToProcesses')
      .leftJoinAndSelect('organizationsToProcesses.process', 'processes')
      .where('organizationsToProcesses.organization.id = :id', { id })
      .getMany();
}
