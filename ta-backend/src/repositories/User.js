"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.UserRepository = void 0;
const typeorm_1 = require("typeorm");
const User_1 = require("@/entities/User");
let UserRepository = class UserRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (user) => this.repository.save(user);
        this.getAll = () => this.repository
            .createQueryBuilder()
            .getMany();
        this.getAllByOrganizationId = (organizationId) => this.repository
            .createQueryBuilder('user')
            .leftJoinAndSelect('user.organization', 'organizations')
            .where('user.organization.id = :id', { id: organizationId })
            .getMany();
        this.getById = (id) => this.repository
            .createQueryBuilder()
            .where('id = :id', { id })
            .getOne();
        this.getByIdWithOrganizationAndRole = (id) => this.repository
            .createQueryBuilder('user')
            .leftJoinAndSelect('user.organization', 'organizations')
            .leftJoinAndSelect('user.role', 'roles')
            .where('user.id = :id', { id })
            .getOne();
        this.getByEmailWithOrganizationAndRole = (email) => this.repository
            .createQueryBuilder('user')
            .leftJoinAndSelect('user.organization', 'organizations')
            .leftJoinAndSelect('user.role', 'roles')
            .where('user.email = :email', { email })
            .getOne();
        this.updateOtpByEmail = (email, otp) => this.repository
            .createQueryBuilder()
            .update()
            .set({ otp })
            .where('email = :email', { email })
            .execute();
    }
};
UserRepository = __decorate([
    typeorm_1.EntityRepository(User_1.User)
], UserRepository);
exports.UserRepository = UserRepository;
//# sourceMappingURL=User.js.map