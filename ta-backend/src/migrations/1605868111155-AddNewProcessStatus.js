"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddNewProcessStatus1605868111155 = void 0;
class AddNewProcessStatus1605868111155 {
    async up(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status DROP DEFAULT`);
        await queryRunner.query(`ALTER TYPE status_type RENAME TO status_type_old`);
        await queryRunner.query(`CREATE TYPE status_type AS ENUM ('active', 'processing', 'finished', 'failed', 'initialized')`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status TYPE status_type USING status::text::status_type`);
        await queryRunner.query(`DROP TYPE status_type_old`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status SET DEFAULT 'initialized'`);
    }
    async down(queryRunner) {
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status DROP DEFAULT`);
        await queryRunner.query(`ALTER TYPE status_type RENAME TO status_type_old`);
        await queryRunner.query(`CREATE TYPE status_type AS ENUM ('active', 'processing', 'finished', 'failed')`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status TYPE status_type USING status::text::status_type`);
        await queryRunner.query(`DROP TYPE status_type_old`);
        await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status SET DEFAULT 'active'`);
    }
}
exports.AddNewProcessStatus1605868111155 = AddNewProcessStatus1605868111155;
//# sourceMappingURL=1605868111155-AddNewProcessStatus.js.map