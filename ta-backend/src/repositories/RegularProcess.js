"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RegularProcessRepository = void 0;
const typeorm_1 = require("typeorm");
const RegularProcess_1 = require("@/entities/RegularProcess");
let RegularProcessRepository = class RegularProcessRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (regularProcess) => this.repository.save(regularProcess);
        this.update = (regularProcess) => this.repository.save(regularProcess);
        this.getById = (id) => this.repository
            .createQueryBuilder()
            .where('id = :id', { id })
            .getOne();
        this.getAllRegular = (organizationId, userId) => {
            const query = this.repository
                .createQueryBuilder('regularProcesses')
                .leftJoinAndSelect('regularProcesses.process', 'processes')
                .leftJoinAndSelect('regularProcesses.user', 'users')
                .leftJoinAndSelect('regularProcesses.organization', 'organizations');
            if (organizationId) {
                query.andWhere('regularProcesses.organization.id = :id', { id: organizationId });
            }
            if (userId) {
                query.andWhere('regularProcesses.user.id = :id', { id: userId });
            }
            return query.getMany();
        };
    }
};
RegularProcessRepository = __decorate([
    typeorm_1.EntityRepository(RegularProcess_1.RegularProcess)
], RegularProcessRepository);
exports.RegularProcessRepository = RegularProcessRepository;
//# sourceMappingURL=RegularProcess.js.map