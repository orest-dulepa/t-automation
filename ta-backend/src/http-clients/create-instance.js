"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createInstance = void 0;
const axios_1 = __importDefault(require("axios"));
exports.createInstance = (baseURL) => {
    const instance = axios_1.default.create({
        baseURL,
        headers: {
            'Content-Type': 'application/json',
        },
    });
    const handleSuccess = ({ data }) => data;
    const handleError = (error) => Promise.reject(error);
    instance.interceptors.response.use(handleSuccess, handleError);
    return instance;
};
//# sourceMappingURL=create-instance.js.map