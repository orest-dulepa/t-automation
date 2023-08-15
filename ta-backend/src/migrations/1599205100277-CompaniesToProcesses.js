"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CompaniesToProcesses1599205100277 = void 0;
class CompaniesToProcesses1599205100277 {
    async up(queryRunner) {
        await queryRunner.query(`CREATE TABLE IF NOT EXISTS companies_to_processes (
		    company_id int NOT NULL,
        process_id int NOT NULL,
        PRIMARY KEY (company_id, process_id),
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (process_id) REFERENCES processes (id))`);
    }
    async down(queryRunner) {
        await queryRunner.query('DROP TABLE IF EXISTS companies_to_processes');
    }
}
exports.CompaniesToProcesses1599205100277 = CompaniesToProcesses1599205100277;
//# sourceMappingURL=1599205100277-CompaniesToProcesses.js.map