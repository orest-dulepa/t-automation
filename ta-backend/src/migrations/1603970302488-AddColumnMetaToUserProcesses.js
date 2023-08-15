"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddColumnMetaToUserProcesses1603970302488 = void 0;
class AddColumnMetaToUserProcesses1603970302488 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ADD meta json NOT NULL DEFAULT '[]'`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN meta`);
    }
}
exports.AddColumnMetaToUserProcesses1603970302488 = AddColumnMetaToUserProcesses1603970302488;
//# sourceMappingURL=1603970302488-AddColumnMetaToUserProcesses.js.map