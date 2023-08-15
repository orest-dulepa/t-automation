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
exports.Log = void 0;
const typeorm_1 = require("typeorm");
const UsersProcesses_1 = require("./UsersProcesses");
let Log = class Log {
    constructor(text, userProcess) {
        this.text = text;
        this.userProcess = userProcess;
    }
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], Log.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({ name: 'text', type: 'text' }),
    __metadata("design:type", String)
], Log.prototype, "text", void 0);
__decorate([
    typeorm_1.OneToOne(() => UsersProcesses_1.UsersProcesses, (usersProcesses) => usersProcesses.id),
    typeorm_1.JoinColumn({ name: 'user_process_id', referencedColumnName: 'id' }),
    __metadata("design:type", UsersProcesses_1.UsersProcesses)
], Log.prototype, "userProcess", void 0);
Log = __decorate([
    typeorm_1.Entity({ name: 'logs' }),
    __metadata("design:paramtypes", [String, UsersProcesses_1.UsersProcesses])
], Log);
exports.Log = Log;
//# sourceMappingURL=Log.js.map