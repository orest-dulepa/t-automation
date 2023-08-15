"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var UsersProcesses_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.UsersProcesses = void 0;
const typeorm_1 = require("typeorm");
const users_processes_1 = require("@/@types/users-processes");
const User_1 = require("./User");
const Organization_1 = require("./Organization");
const Process_1 = require("./Process");
let UsersProcesses = UsersProcesses_1 = class UsersProcesses {
    constructor(processRunId, user, organization, process, meta) {
        this.setId = (id) => {
            this.id = id;
        };
        this.setStatus = (status) => {
            this.status = status;
        };
        this.setCreateTime = (createTime) => {
            this.createTime = createTime;
        };
        this.setStartTime = (startTime) => {
            this.startTime = startTime;
        };
        this.setEndTime = (endTime) => {
            this.endTime = endTime;
        };
        this.setRobocorpRunId = (robocorpId) => {
            this.robocorpId = robocorpId;
        };
        this.setProcessRunId = (processRunId) => {
            this.processRunId = processRunId;
        };
        this.setDuration = (duration) => {
            if (!duration && this.endTime && this.startTime) {
                const endTime = new Date(this.endTime);
                const startTime = new Date(this.startTime);
                this.duration = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
            }
            else if (duration) {
                this.duration = duration;
            }
            console.log('Duration', this.duration);
        };
        this.processRunId = processRunId;
        this.user = user;
        this.createTime = new Date().toISOString();
        this.organization = organization;
        this.process = process;
        this.meta = meta;
    }
};
UsersProcesses.from = (rowUsersProcesses) => {
    const { id, status, createTime, startTime, endTime, processRunId, duration, meta, robocorpId, user: rawUser, organization: rawOrganization, process: rawProcess, } = rowUsersProcesses;
    const user = User_1.User.from(rawUser);
    const organization = Organization_1.Organization.from(rawOrganization);
    const process = Process_1.Process.from(rawProcess);
    const usersProcesses = new UsersProcesses_1(processRunId, user, organization, process, meta);
    usersProcesses.setId(id);
    usersProcesses.setStatus(status);
    usersProcesses.setCreateTime(createTime);
    usersProcesses.setStartTime(startTime);
    usersProcesses.setEndTime(endTime);
    usersProcesses.setDuration(duration);
    usersProcesses.setRobocorpRunId(robocorpId);
    return usersProcesses;
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], UsersProcesses.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({
        name: 'status',
        type: 'enum',
        enum: users_processes_1.PROCESS_STATUS,
        default: users_processes_1.PROCESS_STATUS.INITIALIZED,
    }),
    __metadata("design:type", String)
], UsersProcesses.prototype, "status", void 0);
__decorate([
    typeorm_1.Column({ name: 'create_time', type: 'timestamp' }),
    __metadata("design:type", String)
], UsersProcesses.prototype, "createTime", void 0);
__decorate([
    typeorm_1.Column({ name: 'start_time', type: 'timestamp' }),
    __metadata("design:type", Object)
], UsersProcesses.prototype, "startTime", void 0);
__decorate([
    typeorm_1.Column({ name: 'end_time', type: 'timestamp' }),
    __metadata("design:type", Object)
], UsersProcesses.prototype, "endTime", void 0);
__decorate([
    typeorm_1.Column({ name: 'robocorp_id', type: 'bigint' }),
    __metadata("design:type", Object)
], UsersProcesses.prototype, "robocorpId", void 0);
__decorate([
    typeorm_1.Column({ name: 'process_run_id', type: 'text' }),
    __metadata("design:type", String)
], UsersProcesses.prototype, "processRunId", void 0);
__decorate([
    typeorm_1.Column({ name: 'duration', type: 'bigint' }),
    __metadata("design:type", Object)
], UsersProcesses.prototype, "duration", void 0);
__decorate([
    typeorm_1.Column({ name: 'meta', type: 'json' }),
    __metadata("design:type", Array)
], UsersProcesses.prototype, "meta", void 0);
__decorate([
    typeorm_1.ManyToOne(() => User_1.User, (user) => user.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'user_id', referencedColumnName: 'id' }),
    __metadata("design:type", User_1.User)
], UsersProcesses.prototype, "user", void 0);
__decorate([
    typeorm_1.ManyToOne(() => Organization_1.Organization, (organization) => organization.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'organization_id', referencedColumnName: 'id' }),
    __metadata("design:type", Organization_1.Organization)
], UsersProcesses.prototype, "organization", void 0);
__decorate([
    typeorm_1.ManyToOne(() => Process_1.Process, (process) => process.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'process_id', referencedColumnName: 'id' }),
    __metadata("design:type", Process_1.Process)
], UsersProcesses.prototype, "process", void 0);
UsersProcesses = UsersProcesses_1 = __decorate([
    typeorm_1.Entity({ name: 'users_processes' }),
    __metadata("design:paramtypes", [String, User_1.User, Organization_1.Organization, Process_1.Process, Array])
], UsersProcesses);
exports.UsersProcesses = UsersProcesses;
//# sourceMappingURL=UsersProcesses.js.map