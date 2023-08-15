"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LogRepository = void 0;
const typeorm_1 = require("typeorm");
const Log_1 = require("@/entities/Log");
let LogRepository = class LogRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (log) => this.repository.save(log);
        this.update = (log) => this.repository.save(log);
        this.upsert = async (text, userProcess) => {
            try {
                const existedLog = await this.getByUserProcessId(userProcess.id);
                if (!existedLog) {
                    await this.insert(new Log_1.Log(text, userProcess));
                }
                else {
                    await this.repository
                        .createQueryBuilder()
                        .update(Log_1.Log)
                        .set({ text })
                        .where('userProcess.id = :id', { id: userProcess.id })
                        .execute();
                }
            }
            catch (e) {
                console.log(e);
            }
        };
        this.getByUserProcessId = (id) => this.repository
            .createQueryBuilder('logs')
            .where('logs.userProcess.id = :id', { id })
            .getOne();
    }
};
LogRepository = __decorate([
    typeorm_1.EntityRepository(Log_1.Log)
], LogRepository);
exports.LogRepository = LogRepository;
//# sourceMappingURL=Log.js.map