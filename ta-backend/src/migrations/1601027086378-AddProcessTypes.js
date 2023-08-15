"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddProcessTypes1601027086378 = void 0;
class AddProcessTypes1601027086378 {
    async up(queryRunner) {
        await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE VARCHAR(255);

            DROP TYPE IF EXISTS process_type CASCADE;

            CREATE TYPE process_type AS ENUM ('robocorp', 'uipath_be1', 'uipath_be2');
        `);
        await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE process_type USING (type::process_type);
        `);
    }
    async down(queryRunner) {
        await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE VARCHAR(255);
        `);
        await queryRunner.query(`
            DROP TYPE IF EXISTS process_type CASCADE;
            CREATE TYPE process_type AS ENUM ('robocorp');
        `);
        await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE process_type USING (type::process_type);
        `);
    }
}
exports.AddProcessTypes1601027086378 = AddProcessTypes1601027086378;
//# sourceMappingURL=1601027086378-AddProcessTypes.js.map