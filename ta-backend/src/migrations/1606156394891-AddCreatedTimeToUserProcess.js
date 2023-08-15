"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddCreatedTimeToUserProcess1606156394891 = void 0;
class AddCreatedTimeToUserProcess1606156394891 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ADD COLUMN create_time TIMESTAMP NOT NULL DEFAULT CURRENT_DATE`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN create_time`);
    }
}
exports.AddCreatedTimeToUserProcess1606156394891 = AddCreatedTimeToUserProcess1606156394891;
//# sourceMappingURL=1606156394891-AddCreatedTimeToUserProcess.js.map