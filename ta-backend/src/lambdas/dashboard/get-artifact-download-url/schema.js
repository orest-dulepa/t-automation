"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.artifactDownloadUrlSchema = void 0;
const joi_1 = __importDefault(require("joi"));
exports.artifactDownloadUrlSchema = joi_1.default.object({
    key: joi_1.default.string().required(),
});
//# sourceMappingURL=schema.js.map