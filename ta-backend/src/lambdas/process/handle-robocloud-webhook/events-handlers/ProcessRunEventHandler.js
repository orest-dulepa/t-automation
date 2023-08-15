"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const types_1 = require("../types");
const Handler_1 = __importDefault(require("./Handler"));
class ProcessRunEventHandler extends Handler_1.default {
    constructor() {
        super();
        this.type = types_1.EventsTypes.processRun;
        this.execute = async ({ event, payload }) => {
            console.log(`EXECUTED: ${event} | ${JSON.stringify(payload)}`);
        };
    }
}
exports.default = ProcessRunEventHandler;
//# sourceMappingURL=ProcessRunEventHandler.js.map