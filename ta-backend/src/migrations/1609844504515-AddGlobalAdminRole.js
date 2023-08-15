"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddGlobalAdminRole1609844504515 = void 0;
class AddGlobalAdminRole1609844504515 {
    async up(queryRunner) {
        await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (3, 'admin')
    `);
    }
    async down(queryRunner) {
        await queryRunner.query(`
        DELETE FROM roles
        WHERE id = 3;
    `);
    }
}
exports.AddGlobalAdminRole1609844504515 = AddGlobalAdminRole1609844504515;
//# sourceMappingURL=1609844504515-AddGlobalAdminRole.js.map