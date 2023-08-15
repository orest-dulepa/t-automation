"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.isAxiosError = void 0;
exports.isAxiosError = (e) => {
    if (e.isAxiosError === undefined)
        return false;
    return e.isAxiosError;
};
//# sourceMappingURL=error-type-guard.js.map