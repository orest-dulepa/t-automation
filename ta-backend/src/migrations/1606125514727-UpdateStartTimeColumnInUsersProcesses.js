"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.UpdateStartTimeColumnInUsersProcesses1606125514727 = void 0;
class UpdateStartTimeColumnInUsersProcesses1606125514727 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time DROP NOT NULL`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time DROP DEFAULT`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time SET DEFAULT CURRENT_DATE`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time SET NOT NULL`);
    }
}
exports.UpdateStartTimeColumnInUsersProcesses1606125514727 = UpdateStartTimeColumnInUsersProcesses1606125514727;
//# sourceMappingURL=1606125514727-UpdateStartTimeColumnInUsersProcesses.js.map