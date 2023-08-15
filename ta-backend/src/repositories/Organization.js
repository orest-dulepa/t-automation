"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.OrganizationRepository = void 0;
const typeorm_1 = require("typeorm");
const Organization_1 = require("@/entities/Organization");
let OrganizationRepository = class OrganizationRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (organization) => this.repository.save(organization);
        this.getById = (id) => this.repository
            .createQueryBuilder()
            .where('id = :id', { id })
            .getOne();
        this.getByName = (name) => this.repository
            .createQueryBuilder()
            .where('name = :name', { name })
            .getOne();
        this.update = (organization) => this.repository.save(organization);
        this.delete = (id) => this.repository
            .createQueryBuilder()
            .delete()
            .where('id = :id', { id })
            .execute();
    }
};
OrganizationRepository = __decorate([
    typeorm_1.EntityRepository(Organization_1.Organization)
], OrganizationRepository);
exports.OrganizationRepository = OrganizationRepository;
//# sourceMappingURL=Organization.js.map