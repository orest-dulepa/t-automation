import { AbstractRepository, EntityRepository } from 'typeorm';
import { User } from '@/entities/User';

@EntityRepository(User)
export class UserRepository extends AbstractRepository<User> {
  public insert = (user: User) => this.repository.save(user);

  public getAll = () =>
    this.repository
      .createQueryBuilder()
      .getMany();

  public getAllByOrganizationId = (organizationId: number) =>
    this.repository
      .createQueryBuilder('user')
      .leftJoinAndSelect('user.organization', 'organizations')
      .where('user.organization.id = :id', { id: organizationId })
      .getMany();

  public getById = (id: number) =>
    this.repository
      .createQueryBuilder()
      .where('id = :id', { id })
      .getOne();

  public getByIdWithOrganizationAndRole = (id: number) =>
    this.repository
      .createQueryBuilder('user')
      .leftJoinAndSelect('user.organization', 'organizations')
      .leftJoinAndSelect('user.role', 'roles')
      .where('user.id = :id', { id })
      .getOne();

  public getByEmailWithOrganizationAndRole = (email: string) =>
    this.repository
      .createQueryBuilder('user')
      .leftJoinAndSelect('user.organization', 'organizations')
      .leftJoinAndSelect('user.role', 'roles')
      .where('user.email = :email', { email })
      .getOne();

  public updateOtpByEmail = (email: string, otp: string | null) =>
    this.repository
      .createQueryBuilder()
      .update()
      .set({ otp })
      .where('email = :email', { email })
      .execute();
}
