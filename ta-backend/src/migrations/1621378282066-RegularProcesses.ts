import { MigrationInterface, QueryRunner } from 'typeorm';

export class RegularProcesses1621378282066 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS regular_processes (
          id SERIAL PRIMARY KEY NOT NULL,
          days_of_week json NOT NULL DEFAULT '[]',
          start_time time NOT NULL,
          meta json NOT NULL DEFAULT '[]',
          user_id int NOT NULL,
          process_id int NOT NULL,
          organization_id int NOT NULL,
          FOREIGN KEY (user_id) REFERENCES users (id),
          FOREIGN KEY (process_id) REFERENCES processes (id),
          FOREIGN KEY (organization_id) REFERENCES organizations (id))`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS regular_processes');
  }
}
