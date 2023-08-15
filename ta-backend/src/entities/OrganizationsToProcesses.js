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
exports.OrganizationsToProcesses = void 0;
const typeorm_1 = require("typeorm");
const Organization_1 = require("./Organization");
const Process_1 = require("./Process");
let OrganizationsToProcesses = class OrganizationsToProcesses {
    constructor(organization, process) {
        this.organization = organization;
        this.process = process;
    }
};
__decorate([
    typeorm_1.ManyToOne(() => Organization_1.Organization, (organization) => organization.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'organization_id', referencedColumnName: 'id' }),
    __metadata("design:type", Organization_1.Organization)
], OrganizationsToProcesses.prototype, "organization", void 0);
__decorate([
    typeorm_1.ManyToOne(() => Process_1.Process, (process) => process.id, { primary: true }),
    typeorm_1.JoinColumn({ name: 'process_id', referencedColumnName: 'id' }),
    __metadata("design:type", Process_1.Process)
], OrganizationsToProcesses.prototype, "process", void 0);
OrganizationsToProcesses = __decorate([
    typeorm_1.Entity({ name: 'organizations_to_processes' }),
    __metadata("design:paramtypes", [Organization_1.Organization, Process_1.Process])
], OrganizationsToProcesses);
exports.OrganizationsToProcesses = OrganizationsToProcesses;
//# sourceMappingURL=OrganizationsToProcesses.js.map