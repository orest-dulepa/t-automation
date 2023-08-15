"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyToken = exports.createRefreshToken = exports.createToken = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const auth_1 = require("@/@types/auth");
exports.createToken = (id) => jsonwebtoken_1.default.sign({ type: auth_1.TOKEN_TYPE.ACCESS_TOKEN, id }, process.env.JWT_SECRET, { expiresIn: '1d' });
exports.createRefreshToken = (id) => jsonwebtoken_1.default.sign({ type: auth_1.TOKEN_TYPE.REFRESH_TOKEN, id }, process.env.JWT_SECRET, { expiresIn: '30d' });
exports.verifyToken = (token) => jsonwebtoken_1.default.verify(token, process.env.JWT_SECRET);
//# sourceMappingURL=jwt.js.map