"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddRobocorpRunId1612868410793 = void 0;
class AddRobocorpRunId1612868410793 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ADD robocorp_id int`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN robocorp_id`);
    }
}
exports.AddRobocorpRunId1612868410793 = AddRobocorpRunId1612868410793;
//# sourceMappingURL=1612868410793-AddRobocorpRunId.js.map