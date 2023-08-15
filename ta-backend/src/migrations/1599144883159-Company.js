"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Company1599144883159 = void 0;
class Company1599144883159 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY NOT NULL,
        name text NOT NULL)`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS companies');
    }
}
exports.Company1599144883159 = Company1599144883159;
//# sourceMappingURL=1599144883159-Company.js.map