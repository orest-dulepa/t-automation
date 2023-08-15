import { AbstractRepository, EntityRepository } from 'typeorm';
import { SCHEDULED_PROCESS_STATUS } from '@/@types/scheduled-processes';
import { ScheduledProcess } from '@/entities/ScheduledProcess';

@EntityRepository(ScheduledProcess)
export class ScheduledProcessesRepository extends AbstractRepository<ScheduledProcess> {
  public insert = (scheduledProcess: ScheduledProcess) => this.repository.save(scheduledProcess);

  public getById = (id: number | string) =>
    this.repository
      .createQueryBuilder('scheduledProcesses')
      .leftJoinAndSelect('scheduledProcesses.user', 'users')
      .leftJoinAndSelect('scheduledProcesses.process', 'processes')
      .where('scheduledProcesses.id = :id', { id })
      .getOne();

  public getAllScheduled = (organizationId?: number, userId?: number) => {
    const query = this.repository
      .createQueryBuilder('scheduledProcesses')
      .leftJoinAndSelect('scheduledProcesses.process', 'processes')
      .leftJoinAndSelect('scheduledProcesses.user', 'users')
      .leftJoinAndSelect('scheduledProcesses.organization', 'organizations');

    if (organizationId) {
      query.andWhere('scheduledProcesses.organization.id = :id', { id: organizationId });
    }

    if (userId) {
      query.andWhere('scheduledProcesses.user.id = :id', { id: userId });
    }

    query.andWhere('scheduledProcesses.status = :status', {
      status: SCHEDULED_PROCESS_STATUS.SCHEDULED,
    });

    return query.getMany();
  };

  public updateStatusById = (id: number | string, status: SCHEDULED_PROCESS_STATUS) =>
    this.repository
      .createQueryBuilder()
      .update()
      .set({ status })
      .where('id = :id', { id })
      .execute();
}
