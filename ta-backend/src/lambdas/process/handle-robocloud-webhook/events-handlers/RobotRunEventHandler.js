"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const Event_1 = require("@/entities/Event");
const types_1 = require("../types");
const Handler_1 = __importDefault(require("./Handler"));
class RobotRunEventHandler extends Handler_1.default {
    constructor(usersProcessesRepository, eventRepository) {
        super();
        this.type = types_1.EventsTypes.robotRunEvent;
        this.execute = async ({ payload }) => {
            const { processRunId, seqNo, timeStamp, eventType } = payload;
            const userProcess = await this.usersProcessesRepository.getByProcessRunId(processRunId);
            if (!userProcess) {
                throw new Error(`ERROR: could not found userProcess by processRunId: ${processRunId}`);
            }
            const eventEntity = new Event_1.Event(String(seqNo), timeStamp, eventType, userProcess);
            await this.eventRepository.insert(eventEntity);
        };
        this.usersProcessesRepository = usersProcessesRepository;
        this.eventRepository = eventRepository;
    }
}
exports.default = RobotRunEventHandler;
//# sourceMappingURL=RobotRunEventHandler.js.map