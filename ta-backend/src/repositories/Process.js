"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProcessRepository = void 0;
const typeorm_1 = require("typeorm");
const Process_1 = require("@/entities/Process");
let ProcessRepository = class ProcessRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (process) => this.repository.save(process);
        this.getAll = () => this.repository
            .createQueryBuilder()
            .getMany();
        this.getById = (id) => this.repository
            .createQueryBuilder()
            .where('id = :id', { id })
            .getOne();
        this.update = (process) => this.repository.save(process);
        this.delete = (id) => this.repository
            .createQueryBuilder()
            .delete()
            .where('id = :id', { id })
            .execute();
    }
};
ProcessRepository = __decorate([
    typeorm_1.EntityRepository(Process_1.Process)
], ProcessRepository);
exports.ProcessRepository = ProcessRepository;
//# sourceMappingURL=Process.js.map