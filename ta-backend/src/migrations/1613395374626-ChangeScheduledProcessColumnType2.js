"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeScheduledProcessColumnType21613395374626 = void 0;
class ChangeScheduledProcessColumnType21613395374626 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN IF EXISTS start_time`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ADD COLUMN start_time BIGINT`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN start_time`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ADD COLUMN start_time timestamp with time zone`);
    }
}
exports.ChangeScheduledProcessColumnType21613395374626 = ChangeScheduledProcessColumnType21613395374626;
//# sourceMappingURL=1613395374626-ChangeScheduledProcessColumnType2.js.map