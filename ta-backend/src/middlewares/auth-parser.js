"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.authParser = void 0;
exports.authParser = () => {
    const parse = (handler, next) => {
        const { requestContext } = handler.event;
        const { authorizer } = requestContext;
        authorizer.organization = JSON.parse(authorizer.organization);
        authorizer.role = JSON.parse(authorizer.role);
        next();
    };
    return {
        before: parse,
    };
};
//# sourceMappingURL=auth-parser.js.map