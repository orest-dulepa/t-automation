"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Role1608894674640 = void 0;
class Role1608894674640 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS roles (
          id SERIAL PRIMARY KEY NOT NULL,
          name text NOT NULL UNIQUE)`);
        await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (1, 'employee')
    `);
        await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (2, 'manager')
    `);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS roles');
    }
}
exports.Role1608894674640 = Role1608894674640;
//# sourceMappingURL=1608894674640-Role.js.map