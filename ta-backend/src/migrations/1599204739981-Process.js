"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Process1599204739981 = void 0;
class Process1599204739981 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TYPE process_type AS ENUM ('robocorp')`);
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS processes (
        id SERIAL PRIMARY KEY NOT NULL,
        name text NOT NULL,
        type process_type NOT NULL,
        credentials json NOT NULL,
        properties text[] NOT NULL)`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS processes');
        await queryRunner.query('DROP TYPE IF EXISTS process_type');
    }
}
exports.Process1599204739981 = Process1599204739981;
//# sourceMappingURL=1599204739981-Process.js.map