"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddScheduledProcessStatus1613381845385 = void 0;
class AddScheduledProcessStatus1613381845385 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status DROP DEFAULT`);
        await queryRunner.query(`ALTER TYPE scheduled_process_status_type RENAME TO scheduled_process_status_type_old`);
        await queryRunner.query(`CREATE TYPE scheduled_process_status_type AS ENUM ('scheduled', 'succeeded', 'canceled')`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status TYPE scheduled_process_status_type USING status::text::scheduled_process_status_type`);
        await queryRunner.query(`DROP TYPE scheduled_process_status_type_old`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status SET DEFAULT 'scheduled'`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status DROP DEFAULT`);
        await queryRunner.query(`ALTER TYPE scheduled_process_status_type RENAME TO scheduled_process_status_type_old`);
        await queryRunner.query(`CREATE TYPE scheduled_process_status_type AS ENUM ('scheduled', 'canceled')`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status TYPE scheduled_process_status_type USING status::text::scheduled_process_status_type`);
        await queryRunner.query(`DROP TYPE scheduled_process_status_type_old`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status SET DEFAULT 'scheduled'`);
    }
}
exports.AddScheduledProcessStatus1613381845385 = AddScheduledProcessStatus1613381845385;
//# sourceMappingURL=1613381845385-AddScheduledProcessStatus.js.map