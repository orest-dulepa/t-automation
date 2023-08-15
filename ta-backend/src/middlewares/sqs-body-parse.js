"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sqsBodyParse = void 0;
exports.sqsBodyParse = () => {
    const parse = (handler, next) => {
        const { Records } = handler.event;
        Records[0].body = JSON.parse(Records[0].body);
        next();
    };
    return {
        before: parse,
    };
};
//# sourceMappingURL=sqs-body-parse.js.map