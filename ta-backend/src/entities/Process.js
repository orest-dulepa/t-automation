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
var Process_1;
Object.defineProperty(exports, "__esModule", { value: true });
exports.Process = void 0;
const typeorm_1 = require("typeorm");
const process_1 = require("@/@types/process");
let Process = Process_1 = class Process {
    constructor(name, type, credentials, 
    // credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential,
    properties = []) {
        this.setId = (id) => {
            this.id = id;
        };
        this.setName = (name) => {
            this.name = name;
        };
        this.setType = (type) => {
            this.type = type;
        };
        // public setCredentials = (credentials: IRobocorpCredential | IUIPathCredential | IAWSBotCredential) => {
        //   this.credentials = credentials;
        // };
        this.setProperties = (properties) => {
            this.properties = properties;
        };
        this.name = name;
        this.type = type;
        this.credentials = credentials;
        this.properties = properties;
    }
};
Process.from = (rawProcess) => {
    const { id, name, type, credentials, properties } = rawProcess;
    const process = new Process_1(name, type, credentials, properties);
    process.setId(id);
    return process;
};
__decorate([
    typeorm_1.PrimaryGeneratedColumn(),
    typeorm_1.PrimaryColumn({ name: 'id', type: 'bigint' }),
    __metadata("design:type", Number)
], Process.prototype, "id", void 0);
__decorate([
    typeorm_1.Column({ name: 'name', type: 'text' }),
    __metadata("design:type", String)
], Process.prototype, "name", void 0);
__decorate([
    typeorm_1.Column({
        name: 'type',
        type: 'enum',
        enum: process_1.PROCESS_TYPE,
    }),
    __metadata("design:type", String)
], Process.prototype, "type", void 0);
__decorate([
    typeorm_1.Column({ name: 'credentials', type: 'json' }),
    __metadata("design:type", Object)
], Process.prototype, "credentials", void 0);
__decorate([
    typeorm_1.Column({ name: 'properties', type: 'json' }),
    __metadata("design:type", Array)
], Process.prototype, "properties", void 0);
Process = Process_1 = __decorate([
    typeorm_1.Entity({ name: 'processes' }),
    __metadata("design:paramtypes", [String, String, Object, Array])
], Process);
exports.Process = Process;
//# sourceMappingURL=Process.js.map