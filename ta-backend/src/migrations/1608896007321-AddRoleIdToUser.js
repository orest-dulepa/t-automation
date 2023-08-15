"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddRoleIdToUser1608896007321 = void 0;
class AddRoleIdToUser1608896007321 {
    async up(queryRunner) {
        await queryRunner.query(`
        ALTER TABLE users ADD role_id int NOT NULL DEFAULT 1
      `);
        await queryRunner.query(`
        ALTER TABLE users ADD CONSTRAINT role_id FOREIGN KEY (role_id) REFERENCES roles (id)
      `);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users DROP COLUMN role_id`);
    }
}
exports.AddRoleIdToUser1608896007321 = AddRoleIdToUser1608896007321;
//# sourceMappingURL=1608896007321-AddRoleIdToUser.js.map