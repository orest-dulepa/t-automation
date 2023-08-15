"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DropUsersProccesLogsAndEventsColumns1601380388193 = void 0;
class DropUsersProccesLogsAndEventsColumns1601380388193 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN events_source`);
        await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN logs_source`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ADD events_source text`);
        await queryRunner.query(`ALTER TABLE users_processes ADD logs_source text`);
    }
}
exports.DropUsersProccesLogsAndEventsColumns1601380388193 = DropUsersProccesLogsAndEventsColumns1601380388193;
//# sourceMappingURL=1601380388193-DropUsersProcessesLogsAndEventsColumns.js.map