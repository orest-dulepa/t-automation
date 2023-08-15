"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EventRepository = void 0;
const typeorm_1 = require("typeorm");
const Event_1 = require("@/entities/Event");
let EventRepository = class EventRepository extends typeorm_1.AbstractRepository {
    constructor() {
        super(...arguments);
        this.insert = (event) => this.repository.save(event);
        this.getAllByUserProcessId = (id) => this.repository
            .createQueryBuilder('events')
            .where('events.userProcess.id = :id', { id })
            .getMany();
    }
};
EventRepository = __decorate([
    typeorm_1.EntityRepository(Event_1.Event)
], EventRepository);
exports.EventRepository = EventRepository;
//# sourceMappingURL=Event.js.map