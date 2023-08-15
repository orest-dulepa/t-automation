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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ScheduledProcess = void 0;
const typeorm_1 = require("typeorm");
const scheduled_processes_1 = require("@/@types/scheduled-processes");
const User_1 = require("./User");
const Process_1 = require("./Process");
const Organization_1 = require("./Organization");
let ScheduledProcess = class ScheduledProcess {
    constructor(meta, startTime, user, process, organization) {
        this.meta = meta;
        this.startTime = startTime;
        this.user = user;
        this.process = process;
        this.organization = organization;
    }
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], ScheduledProcess.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({
        name: 'status',
        type: 'enum',
        enum: scheduled_processes_1.SCHEDULED_PROCESS_STATUS,
        default: scheduled_processes_1.SCHEDULED_PROCESS_STATUS.SCHEDULED,
    }),
    __metadata("design:type", String)
], ScheduledProcess.prototype, "status", void 0);
__decorate([
    typeorm_1.Column({ name: 'meta', type: 'json' }),
    __metadata("design:type", Array)
], ScheduledProcess.prototype, "meta", void 0);
__decorate([
    typeorm_1.Column({ name: 'start_time', type: 'bigint' }),
    __metadata("design:type", Number)
], ScheduledProcess.prototype, "startTime", void 0);
__decorate([
    typeorm_1.ManyToOne(() => User_1.User, (user) => user.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'user_id', referencedColumnName: 'id' }),
    __metadata("design:type", User_1.User)
], ScheduledProcess.prototype, "user", void 0);
__decorate([
    typeorm_1.ManyToOne(() => Process_1.Process, (process) => process.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'process_id', referencedColumnName: 'id' }),
    __metadata("design:type", Process_1.Process)
], ScheduledProcess.prototype, "process", void 0);
__decorate([
    typeorm_1.ManyToOne(() => Organization_1.Organization, (organization) => organization.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'organization_id', referencedColumnName: 'id' }),
    __metadata("design:type", Organization_1.Organization)
], ScheduledProcess.prototype, "organization", void 0);
ScheduledProcess = __decorate([
    typeorm_1.Entity({ name: 'scheduled_processes' }),
    __metadata("design:paramtypes", [Array, Number, User_1.User,
        Process_1.Process,
        Organization_1.Organization])
], ScheduledProcess);
exports.ScheduledProcess = ScheduledProcess;
//# sourceMappingURL=ScheduledProcess.js.map