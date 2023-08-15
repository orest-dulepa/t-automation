"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.errorHandler = void 0;
const boom_1 = require("@hapi/boom");
exports.errorHandler = () => {
    const handleError = (handler, next) => {
        var _a, _b, _c;
        const { error } = handler;
        let statusCode;
        let msg;
        console.log((_c = (_b = (_a = error) === null || _a === void 0 ? void 0 : _a.response) === null || _b === void 0 ? void 0 : _b.data) === null || _c === void 0 ? void 0 : _c.error);
        if (boom_1.isBoom(error)) {
            const { output, message } = error;
            statusCode = output.statusCode;
            msg = message;
        }
        else {
            statusCode = 500;
            msg = (error === null || error === void 0 ? void 0 : error.message) || 'Something went wrong';
        }
        handler.response = {
            statusCode,
            body: JSON.stringify({ msg }),
        };
        next();
    };
    return {
        onError: handleError,
    };
};
//# sourceMappingURL=error-handler.js.map