"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeProcessesPropertiesColumnType1601387759163 = void 0;
class ChangeProcessesPropertiesColumnType1601387759163 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE processes DROP COLUMN properties`);
        await queryRunner.query(`ALTER TABLE processes ADD properties json NOT NULL DEFAULT '[]'`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE processes DROP COLUMN properties`);
        await queryRunner.query(`ALTER TABLE processes ADD properties text[] NOT NULL DEFAULT '{}'`);
    }
}
exports.ChangeProcessesPropertiesColumnType1601387759163 = ChangeProcessesPropertiesColumnType1601387759163;
//# sourceMappingURL=1601387759163-ChangeProcessesPropertiesColumnType.js.map