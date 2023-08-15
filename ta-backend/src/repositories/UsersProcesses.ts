import {AbstractRepository, Brackets, EntityRepository} from 'typeorm';
import {PROCESS_STATUS} from '@/@types/users-processes';
import {RowUsersProcesses, UsersProcesses} from '@/entities/UsersProcesses';

@EntityRepository(UsersProcesses)
export class UsersProcessesRepository extends AbstractRepository<UsersProcesses> {
  public insert = (usersProcesses: UsersProcesses) => this.repository.save(usersProcesses);

  public getAllByUserId = (id: number) =>
    this.repository
      .createQueryBuilder('usersProcesses')
      .where('usersProcesses.user.id = :id', { id })
      .getMany();

  public getById = (id: number | string) =>
    this.repository
      .createQueryBuilder('usersProcesses')
      .leftJoinAndSelect('usersProcesses.user', 'users')
      .leftJoinAndSelect('usersProcesses.process', 'processes')
      .leftJoinAndSelect('usersProcesses.organization', 'organizations')
      .where('usersProcesses.id = :id', { id })
      .getOne();

  public getByProcessRunId = (processRunId: number | string) =>
    this.repository
      .createQueryBuilder('usersProcesses')
      .leftJoinAndSelect('usersProcesses.user', 'users')
      .leftJoinAndSelect('usersProcesses.process', 'processes')
      .leftJoinAndSelect('usersProcesses.organization', 'organizations')
      .where('usersProcesses.processRunId = :processRunId', { processRunId })
      .getOne();

  public getAllRunning = (organizationId?: number, userId?: number) => {
    const query = this.repository
      .createQueryBuilder('usersProcesses')
      .leftJoinAndSelect('usersProcesses.process', 'processes')
      .leftJoinAndSelect('usersProcesses.user', 'users');


    if (organizationId) {
      query.andWhere('usersProcesses.organization.id = :id', { id: organizationId });
    }

    if (userId) {
      query.andWhere('usersProcesses.user.id = :id', { id: userId });
    }

    query
      .andWhere(new Brackets(qb => {
          qb.where('usersProcesses.status = :active',  { active: PROCESS_STATUS.ACTIVE })
            .orWhere('usersProcesses.status = :processing',  { processing: PROCESS_STATUS.PROCESSING })
            .orWhere('usersProcesses.status = :initialized',  { initialized: PROCESS_STATUS.INITIALIZED })
      }));

    return query.getMany();
  };

  public getAllCompleted = (
    organizationId?: number,
    userId?: number,
    processes_filter?: string,
    statuses_filter?: string,
    inputs_filter?: string,
    end_times_filter?: string,
    executed_by_filter?: string,
    processes_sort?: '0' | '1',
    run_number_sort?: '0' | '1',
    duration_sort?: '0' | '1',
    end_times_sort?: '0' | '1',
    executed_by_sort?: '0' | '1',
    amount?: string,
    page?: string,
  ) => {
    const query = this.repository
      .createQueryBuilder('usersProcesses')
      .leftJoinAndSelect('usersProcesses.process', 'processes')
      .leftJoinAndSelect('usersProcesses.user', 'users');

    if (organizationId) {
      query.andWhere('usersProcesses.organization.id = :id', { id: organizationId });
    }

    if (userId) {
      query.andWhere('usersProcesses.user.id = :id', { id: userId });
    }

    if (statuses_filter) {
      const statuses = statuses_filter.split(';');

      query.andWhere(
        new Brackets((qb) => {
          statuses.forEach((status, index) => {
            qb.orWhere(`usersProcesses.status = :status-${index}`, { [`status-${index}`]: status });
          });
        }),
      );
    } else {
      query.andWhere(
        new Brackets((qb) => {
          qb.where('usersProcesses.status = :finished', { finished: PROCESS_STATUS.FINISHED })
            .orWhere('usersProcesses.status = :failed', { failed: PROCESS_STATUS.FAILED })
            .orWhere('usersProcesses.status = :warning', { warning: PROCESS_STATUS.WARNING });
        }),
      );
    }

    if (processes_filter) {
      const processesIds = processes_filter.split(';');

      query.andWhere(
        new Brackets((qb) => {
          processesIds.forEach((processId, index) => {
            qb.orWhere(`usersProcesses.process.id = :process-id-${index}`, { [`process-id-${index}`]: processId });
          });
        }),
      );
    }

    if (inputs_filter) {
      const values = inputs_filter.split(';');

      query.andWhere(
        new Brackets((qb) => {
          values.forEach((value, index) => {
            qb.orWhere(`usersProcesses.meta ::jsonb @> :meta-${index}`, { [`meta-${index}`]: `[{"value":"${value}"}]` });
          });
        }),
      );
    }

    if (end_times_filter) {
      // Can be per day: timestamp;timestamp...
      // OR per day + range: timestamp;timestamp-timestamp...
      const endTimes = end_times_filter.split(';');

      query.andWhere(
        new Brackets((qb) => {
          endTimes.forEach((endTime, index) => {
            const splitEndTime = endTime.split('-');

            if (splitEndTime.length === 2) {
              const [from, to] = splitEndTime;

              qb
                .orWhere(`DATE(usersProcesses.endTime) >= :startRangeTime-${index}`, { [`startRangeTime-${index}`]: new Date(Number(from)) })
                .andWhere(`DATE(usersProcesses.endTime) <= :endRangeTime-${index}`, { [`endRangeTime-${index}`]: new Date(Number(to)) })
            } else {
              qb.orWhere(`DATE(usersProcesses.endTime) = :endTime-${index}`, { [`endTime-${index}`]: new Date(Number(endTime)) });
            }
          });
        }),
      );
    }

    if (executed_by_filter) {
      const usersIds = executed_by_filter.split(';');

      query.andWhere(
        new Brackets((qb) => {
          usersIds.forEach((userId, index) => {
            qb.orWhere(`usersProcesses.user.id = :executedBy-id-${index}`, { [`executedBy-id-${index}`]: userId });
          });
        }),
      );
    }

    switch (true) {
      case processes_sort === '0': {
        query.orderBy('processes.name', 'ASC');
        break;
      }
      case processes_sort === '1': {
        query.orderBy('processes.name', 'DESC');
        break;
      }
    }

    switch (true) {
      case run_number_sort === '0': {
        query.orderBy('usersProcesses.id', 'ASC');
        break;
      }
      case run_number_sort === '1': {
        query.orderBy('usersProcesses.id', 'DESC');
        break;
      }
    }

    switch (true) {
      case duration_sort === '0': {
        query.orderBy('usersProcesses.duration', 'ASC');
        break;
      }
      case duration_sort === '1': {
        query.orderBy('usersProcesses.duration', 'DESC');
        break;
      }
    }

    switch (true) {
      case end_times_sort === '0': {
        query.orderBy('usersProcesses.endTime', 'ASC');
        break;
      }
      case end_times_sort === '1': {
        query.orderBy('usersProcesses.endTime', 'DESC');
        break;
      }
    }

    switch (true) {
      case executed_by_sort === '0': {
        query.orderBy('users.email', 'ASC');
        break;
      }
      case executed_by_sort === '1': {
        query.orderBy('users.email', 'DESC');
        break;
      }
    }

    const numericAmount = Number(amount);
    const numericPage = Number(page);

    if (!Number.isNaN(numericAmount) && !Number.isNaN(numericPage)) {
      const offset = (numericPage - 1) * numericAmount;

      query.offset(offset).limit(numericAmount);
    }

    return query.getManyAndCount();
  };

  public getProcessing = () =>
    this.repository.find({
      relations: ['user', 'process', 'organization', 'user.organization'],
      where: [
        { status: PROCESS_STATUS.PROCESSING },
      ],
    });

  public update = (usersProcesses: UsersProcesses | RowUsersProcesses) => {
    const { id, status, createTime, startTime, endTime, processRunId, duration, meta, robocorpId } = usersProcesses;

    return this.repository
      .createQueryBuilder()
      .update({
        id,
        status,
        createTime,
        startTime,
        endTime,
        processRunId,
        duration,
        meta,
        robocorpId,
      })
      .where('id = :id', { id: usersProcesses.id })
      .execute();
  }
}
