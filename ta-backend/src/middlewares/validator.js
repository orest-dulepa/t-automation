"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validator = void 0;
const boom_1 = require("@hapi/boom");
exports.validator = (schema) => {
    const validate = (handler, next) => {
        const { body } = handler.event;
        const { error } = schema.validate(body || {});
        if (error) {
            throw boom_1.badRequest(error.message);
        }
        next();
    };
    return {
        before: validate,
    };
};
//# sourceMappingURL=validator.js.map