"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.User1599204666261 = void 0;
class User1599204666261 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY NOT NULL,
        email text NOT NULL UNIQUE,
        first_name text NOT NULL,
        last_name text NOT NULL,
        company_id int NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies (id),
        otp text)`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS users');
    }
}
exports.User1599204666261 = User1599204666261;
//# sourceMappingURL=1599204666261-User.js.map