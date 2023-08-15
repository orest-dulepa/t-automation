"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.processUpdateSchema = void 0;
const joi_1 = __importDefault(require("joi"));
const process_1 = require("@/@types/process");
const propertiesSchema = joi_1.default.object({
    api_name: joi_1.default.string().required(),
    name: joi_1.default.string().required(),
    type: joi_1.default.string().required(),
});
exports.processUpdateSchema = joi_1.default.object({
    name: joi_1.default.string(),
    type: joi_1.default.string().valid(process_1.PROCESS_TYPE.ROBOCORP),
    // type: Joi.string().valid(PROCESS_TYPE.ROBOCORP, PROCESS_TYPE.UIPATH_BE1, PROCESS_TYPE.UIPATH_BE2),
    properties: joi_1.default.array().items(propertiesSchema),
});
//# sourceMappingURL=schema.js.map