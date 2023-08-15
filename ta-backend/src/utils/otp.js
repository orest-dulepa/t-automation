"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateOTP = void 0;
exports.generateOTP = () => {
    const getRandomInRange = (min, max) => Math.floor(Math.random() * (max - min) + min);
    return String(getRandomInRange(100000, 999999));
};
//# sourceMappingURL=otp.js.map