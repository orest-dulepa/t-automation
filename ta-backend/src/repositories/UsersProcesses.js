"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.UsersProcessesRepository = void 0;
const typeorm_1 = require("typeorm");
const users_processes_1 = require("@/@types/users-processes");
const UsersProcesses_1 = require("@/entities/UsersProcesses");
let UsersProcessesRepository = class UsersProcessesRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (usersProcesses) => this.repository.save(usersProcesses);
        this.getAllByUserId = (id) => this.repository
            .createQueryBuilder('usersProcesses')
            .where('usersProcesses.user.id = :id', { id })
            .getMany();
        this.getById = (id) => this.repository
            .createQueryBuilder('usersProcesses')
            .leftJoinAndSelect('usersProcesses.user', 'users')
            .leftJoinAndSelect('usersProcesses.process', 'processes')
            .leftJoinAndSelect('usersProcesses.organization', 'organizations')
            .where('usersProcesses.id = :id', { id })
            .getOne();
        this.getByProcessRunId = (processRunId) => this.repository
            .createQueryBuilder('usersProcesses')
            .leftJoinAndSelect('usersProcesses.user', 'users')
            .leftJoinAndSelect('usersProcesses.process', 'processes')
            .leftJoinAndSelect('usersProcesses.organization', 'organizations')
            .where('usersProcesses.processRunId = :processRunId', { processRunId })
            .getOne();
        this.getAllRunning = (organizationId, userId) => {
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
                .andWhere(new typeorm_1.Brackets(qb => {
                qb.where('usersProcesses.status = :active', { active: users_processes_1.PROCESS_STATUS.ACTIVE })
                    .orWhere('usersProcesses.status = :processing', { processing: users_processes_1.PROCESS_STATUS.PROCESSING })
                    .orWhere('usersProcesses.status = :initialized', { initialized: users_processes_1.PROCESS_STATUS.INITIALIZED });
            }));
            return query.getMany();
        };
        this.getAllCompleted = (organizationId, userId, processes_filter, statuses_filter, inputs_filter, end_times_filter, executed_by_filter, processes_sort, run_number_sort, duration_sort, end_times_sort, executed_by_sort, amount, page) => {
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
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    statuses.forEach((status, index) => {
                        qb.orWhere(`usersProcesses.status = :status-${index}`, { [`status-${index}`]: status });
                    });
                }));
            }
            else {
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    qb.where('usersProcesses.status = :finished', { finished: users_processes_1.PROCESS_STATUS.FINISHED })
                        .orWhere('usersProcesses.status = :failed', { failed: users_processes_1.PROCESS_STATUS.FAILED })
                        .orWhere('usersProcesses.status = :warning', { warning: users_processes_1.PROCESS_STATUS.WARNING });
                }));
            }
            if (processes_filter) {
                const processesIds = processes_filter.split(';');
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    processesIds.forEach((processId, index) => {
                        qb.orWhere(`usersProcesses.process.id = :process-id-${index}`, { [`process-id-${index}`]: processId });
                    });
                }));
            }
            if (inputs_filter) {
                const values = inputs_filter.split(';');
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    values.forEach((value, index) => {
                        qb.orWhere(`usersProcesses.meta ::jsonb @> :meta-${index}`, { [`meta-${index}`]: `[{"value":"${value}"}]` });
                    });
                }));
            }
            if (end_times_filter) {
                // Can be per day: timestamp;timestamp...
                // OR per day + range: timestamp;timestamp-timestamp...
                const endTimes = end_times_filter.split(';');
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    endTimes.forEach((endTime, index) => {
                        const splitEndTime = endTime.split('-');
                        if (splitEndTime.length === 2) {
                            const [from, to] = splitEndTime;
                            qb
                                .orWhere(`DATE(usersProcesses.endTime) >= :startRangeTime-${index}`, { [`startRangeTime-${index}`]: new Date(Number(from)) })
                                .andWhere(`DATE(usersProcesses.endTime) <= :endRangeTime-${index}`, { [`endRangeTime-${index}`]: new Date(Number(to)) });
                        }
                        else {
                            qb.orWhere(`DATE(usersProcesses.endTime) = :endTime-${index}`, { [`endTime-${index}`]: new Date(Number(endTime)) });
                        }
                    });
                }));
            }
            if (executed_by_filter) {
                const usersIds = executed_by_filter.split(';');
                query.andWhere(new typeorm_1.Brackets((qb) => {
                    usersIds.forEach((userId, index) => {
                        qb.orWhere(`usersProcesses.user.id = :executedBy-id-${index}`, { [`executedBy-id-${index}`]: userId });
                    });
                }));
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
        this.getProcessing = () => this.repository.find({
            relations: ['user', 'process', 'organization', 'user.organization'],
            where: [
                { status: users_processes_1.PROCESS_STATUS.PROCESSING },
            ],
        });
        this.update = (usersProcesses) => {
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
        };
    }
};
UsersProcessesRepository = __decorate([
    typeorm_1.EntityRepository(UsersProcesses_1.UsersProcesses)
], UsersProcessesRepository);
exports.UsersProcessesRepository = UsersProcessesRepository;
//# sourceMappingURL=UsersProcesses.js.map