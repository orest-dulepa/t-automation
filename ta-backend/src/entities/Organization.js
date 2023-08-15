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
var Organization_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.Organization = void 0;
const typeorm_1 = require("typeorm");
const OrganizationsToProcesses_1 = require("./OrganizationsToProcesses");
let Organization = Organization_1 = class Organization {
    constructor(name) {
        this.setId = (id) => {
            this.id = id;
        };
        this.setName = (name) => {
            this.name = name;
        };
        this.name = name;
    }
};
Organization.from = (rawOrganization) => {
    const { id, name } = rawOrganization;
    const organization = new Organization_1(name);
    organization.setId(id);
    return organization;
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], Organization.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({ name: 'name', type: 'text' }),
    __metadata("design:type", String)
], Organization.prototype, "name", void 0);
__decorate([
    typeorm_1.OneToMany(() => OrganizationsToProcesses_1.OrganizationsToProcesses, (organizationsToProcesses) => organizationsToProcesses.organization),
    __metadata("design:type", Array)
], Organization.prototype, "organizationToProcesses", void 0);
Organization = Organization_1 = __decorate([
    typeorm_1.Entity({ name: 'organizations' }),
    __metadata("design:paramtypes", [String])
], Organization);
exports.Organization = Organization;
//# sourceMappingURL=Organization.js.map