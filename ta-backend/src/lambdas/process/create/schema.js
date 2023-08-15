"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.processCreateSchema = void 0;
const joi_1 = __importDefault(require("joi"));
const process_1 = require("@/@types/process");
const robocorpCredentialSchema = joi_1.default.object({
    server: joi_1.default.string().required(),
    apiProcessId: joi_1.default.string().required(),
    apiWorkspace: joi_1.default.string().required(),
    rcWskey: joi_1.default.string().required(),
});
// const uiPathCredentialBE1Schema = Joi.object<IUIPathCredentialBE1>({
//   tenancyName: Joi.string().required(),
//   usernameOrEmailAddress: Joi.string().required(),
//   password: Joi.string().required(),
//   robotIds: Joi.array().items(Joi.number()).required(),
//   release: Joi.string().required(),
// });
// const uiPathCredentialBE2Schema = Joi.object<IUIPathCredentialBE2>({
//   tenancyName: Joi.string().required(),
//   usernameOrEmailAddress: Joi.string().required(),
//   password: Joi.string().required(),
//   botName: Joi.string().required(),
// });
const propertiesSchema = joi_1.default.object({
    api_name: joi_1.default.string().required(),
    name: joi_1.default.string().required(),
    type: joi_1.default.string().required(),
});
exports.processCreateSchema = joi_1.default.object({
    name: joi_1.default.string().required(),
    type: joi_1.default.string()
        // .valid(PROCESS_TYPE.ROBOCORP, PROCESS_TYPE.UIPATH_BE1, PROCESS_TYPE.UIPATH_BE2)
        .valid(process_1.PROCESS_TYPE.ROBOCORP)
        .required(),
    credentials: joi_1.default.alternatives().try(robocorpCredentialSchema),
    properties: joi_1.default.array().items(propertiesSchema).required(),
});
//# sourceMappingURL=schema.js.map