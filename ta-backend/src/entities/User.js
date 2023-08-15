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
var User_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.User = void 0;
const typeorm_1 = require("typeorm");
const Organization_1 = require("./Organization");
const UsersProcesses_1 = require("./UsersProcesses");
const Role_1 = require("./Role");
let User = User_1 = class User {
    constructor(email, firstName, lastName, organization) {
        this.setId = (id) => {
            this.id = id;
        };
        this.setEmail = (email) => {
            this.email = email;
        };
        this.setFirstName = (firstName) => {
            this.firstName = firstName;
        };
        this.setLastName = (lastName) => {
            this.lastName = lastName;
        };
        this.setOtp = (otp) => {
            this.otp = otp;
        };
        this.email = email;
        this.firstName = firstName;
        this.lastName = lastName;
        this.organization = organization;
    }
};
User.from = (rawUser) => {
    const { id, email, firstName, lastName, organization: rawOrganization } = rawUser;
    const organization = Organization_1.Organization.from(rawOrganization);
    const user = new User_1(email, firstName, lastName, organization);
    user.setId(id);
    return user;
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], User.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({ name: 'email', type: 'text', unique: true }),
    __metadata("design:type", String)
], User.prototype, "email", void 0);
__decorate([
    typeorm_1.Column({ name: 'first_name', type: 'text' }),
    __metadata("design:type", String)
], User.prototype, "firstName", void 0);
__decorate([
    typeorm_1.Column({ name: 'last_name', type: 'text' }),
    __metadata("design:type", String)
], User.prototype, "lastName", void 0);
__decorate([
    typeorm_1.Column({ name: 'otp', type: 'text', nullable: true }),
    __metadata("design:type", Object)
], User.prototype, "otp", void 0);
__decorate([
    typeorm_1.OneToOne(() => Organization_1.Organization, (organization) => organization.id),
    typeorm_1.JoinColumn({ name: 'organization_id', referencedColumnName: 'id' }),
    __metadata("design:type", Organization_1.Organization)
], User.prototype, "organization", void 0);
__decorate([
    typeorm_1.OneToOne(() => Role_1.Role, (role) => role.id),
    typeorm_1.JoinColumn({ name: 'role_id', referencedColumnName: 'id' }),
    __metadata("design:type", Role_1.Role)
], User.prototype, "role", void 0);
__decorate([
    typeorm_1.OneToMany(() => UsersProcesses_1.UsersProcesses, (usersProcesses) => usersProcesses.user),
    __metadata("design:type", Array)
], User.prototype, "usersProcesses", void 0);
User = User_1 = __decorate([
    typeorm_1.Entity({ name: 'users' }),
    __metadata("design:paramtypes", [String, String, String, Organization_1.Organization])
], User);
exports.User = User;
//# sourceMappingURL=User.js.map