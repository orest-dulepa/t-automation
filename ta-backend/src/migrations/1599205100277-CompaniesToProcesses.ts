import { MigrationInterface, QueryRunner } from 'typeorm';

export class CompaniesToProcesses1599205100277 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS companies_to_processes (
		    company_id int NOT NULL,
        process_id int NOT NULL,
        PRIMARY KEY (company_id, process_id),
        FOREIGN KEY (company_id) REFERENCES companies (id),
        FOREIGN KEY (process_id) REFERENCES processes (id))`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS companies_to_processes');
  }
}
