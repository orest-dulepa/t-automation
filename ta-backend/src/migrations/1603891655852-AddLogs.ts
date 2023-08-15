import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddLogs1603891655852 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY NOT NULL,
                text text NOT NULL,
                user_process_id int NOT NULL,
                FOREIGN KEY (user_process_id) REFERENCES users_processes (id))`,
    );

    await queryRunner.query(`CREATE INDEX idx_user_process_id_on_logs ON logs (user_process_id)`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP INDEX IF EXISTS idx_user_process_id_on_logs');

    await queryRunner.query('DROP TABLE IF EXISTS logs');
  }
}
