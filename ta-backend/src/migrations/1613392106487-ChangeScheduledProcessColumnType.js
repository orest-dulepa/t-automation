"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeScheduledProcessColumnType1613392106487 = void 0;
class ChangeScheduledProcessColumnType1613392106487 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN start_time TYPE TIMESTAMP with time zone`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN start_time TYPE TIMESTAMP`);
    }
}
exports.ChangeScheduledProcessColumnType1613392106487 = ChangeScheduledProcessColumnType1613392106487;
//# sourceMappingURL=1613392106487-ChangeScheduledProcessColumnType.js.map