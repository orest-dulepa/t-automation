"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddLogs1603891655852 = void 0;
class AddLogs1603891655852 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY NOT NULL,
                text text NOT NULL,
                user_process_id int NOT NULL,
                FOREIGN KEY (user_process_id) REFERENCES users_processes (id))`);
        await queryRunner.query(`CREATE INDEX idx_user_process_id_on_logs ON logs (user_process_id)`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP INDEX IF EXISTS idx_user_process_id_on_logs');
        await queryRunner.query('DROP TABLE IF EXISTS logs');
    }
}
exports.AddLogs1603891655852 = AddLogs1603891655852;
//# sourceMappingURL=1603891655852-AddLogs.js.map