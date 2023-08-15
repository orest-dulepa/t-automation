import { AbstractRepository, EntityRepository } from 'typeorm';
import { Organization } from '@/entities/Organization';

@EntityRepository(Organization)
export class OrganizationRepository extends AbstractRepository<Organization> {
  public insert = (organization: Organization) => this.repository.save(organization);

  public getById = (id: string | number) =>
    this.repository
      .createQueryBuilder()
      .where('id = :id', { id })
      .getOne();

  public getByName = (name: string) =>
    this.repository
      .createQueryBuilder()
      .where('name = :name', { name })
      .getOne();

  public update = (organization: Organization) => this.repository.save(organization);

  public delete = (id: string) =>
    this.repository
      .createQueryBuilder()
      .delete()
      .where('id = :id', { id })
      .execute();
}
