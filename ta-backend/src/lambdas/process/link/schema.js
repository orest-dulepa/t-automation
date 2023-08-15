"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.processLinkSchema = void 0;
const joi_1 = __importDefault(require("joi"));
exports.processLinkSchema = joi_1.default.object({
    organizationId: joi_1.default.number().required(),
    processId: joi_1.default.number().required(),
});
//# sourceMappingURL=schema.js.map