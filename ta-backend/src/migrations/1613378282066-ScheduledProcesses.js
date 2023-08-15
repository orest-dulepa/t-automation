"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ScheduledProcesses1613378282066 = void 0;
class ScheduledProcesses1613378282066 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TYPE scheduled_process_status_type AS ENUM ('scheduled', 'canceled')`);
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS scheduled_processes (
          id SERIAL PRIMARY KEY NOT NULL,
          status scheduled_process_status_type NOT NULL DEFAULT 'scheduled',
          meta json NOT NULL DEFAULT '[]',
          user_id int NOT NULL,
          process_id int NOT NULL,
          FOREIGN KEY (user_id) REFERENCES users (id),
          FOREIGN KEY (process_id) REFERENCES processes (id))`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS scheduled_processes');
        await queryRunner.query('DROP TYPE IF EXISTS scheduled_process_status_type');
    }
}
exports.ScheduledProcesses1613378282066 = ScheduledProcesses1613378282066;
//# sourceMappingURL=1613378282066-ScheduledProcesses.js.map