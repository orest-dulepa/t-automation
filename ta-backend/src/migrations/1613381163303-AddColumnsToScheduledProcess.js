"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddColumnsToScheduledProcess1613381163303 = void 0;
class AddColumnsToScheduledProcess1613381163303 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes ADD COLUMN start_time TIMESTAMP NOT NULL`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ADD organization_id int NOT NULL`);
        await queryRunner.query(`ALTER TABLE scheduled_processes ADD CONSTRAINT organization_id FOREIGN KEY (organization_id) REFERENCES organizations (id)`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN start_time`);
        await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN organization_id`);
    }
}
exports.AddColumnsToScheduledProcess1613381163303 = AddColumnsToScheduledProcess1613381163303;
//# sourceMappingURL=1613381163303-AddColumnsToScheduledProcess.js.map