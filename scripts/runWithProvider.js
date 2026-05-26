const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

async function main() {
  const provider = process.env.DATABASE_PROVIDER || 'postgresql';
  const schemaPath = path.join(__dirname, `${provider}-schema.prisma`);
  const targetPath = path.join(__dirname, 'schema.prisma');

  // Restore the normal Evolution API behavior of copying the schema
  if (fs.existsSync(schemaPath)) {
    fs.copyFileSync(schemaPath, targetPath);
  }

  // Pre-migration baseline check to prevent P3005 error
  if (provider === 'postgresql' && process.env.DATABASE_URL) {
    const client = new Client({ connectionString: process.env.DATABASE_URL });
    try {
      await client.connect();
      
      const res = await client.query(`
        SELECT EXISTS (
          SELECT FROM information_schema.tables 
          WHERE table_schema = 'public' 
          AND table_name = '_prisma_migrations'
        );
      `);
      
      const migrationsTableExists = res.rows[0].exists;
      let shouldBaseline = false;

      if (migrationsTableExists) {
        // Table exists, verify if it's empty or has missing migrations
        const countRes = await client.query('SELECT COUNT(*) FROM _prisma_migrations;');
        const migrationCount = parseInt(countRes.rows[0].count, 10);
        
        // Let's also check if there are actual tables in the DB
        const tablesRes = await client.query(`
          SELECT count(*) as count FROM information_schema.tables 
          WHERE table_schema = 'public' AND table_name != '_prisma_migrations';
        `);
        const hasOtherTables = parseInt(tablesRes.rows[0].count, 10) > 0;

        if (hasOtherTables) {
          console.log(`[Baseline Check] Found _prisma_migrations with ${migrationCount} records and populated database.`);
          shouldBaseline = true;
        } else {
           console.log(`[Baseline Check] Database is empty. Proceeding normally.`);
        }
      } else {
        console.log(`[Baseline Check] _prisma_migrations table does not exist. Proceeding normally.`);
      }

      if (shouldBaseline) {
        console.log("[Baseline Check] Baselining pending migrations to resolve P3005...");
        const migrationsDir = path.join(__dirname, 'postgresql-migrations');
        if (fs.existsSync(migrationsDir)) {
          const migrations = fs.readdirSync(migrationsDir)
            .filter(file => fs.statSync(path.join(migrationsDir, file)).isDirectory())
            .sort();
          
          for (const migration of migrations) {
            console.log(`[Baseline Check] Resolving migration: ${migration}`);
            try {
              execSync(`npx prisma migrate resolve --applied "${migration}" --schema ${schemaPath}`, { stdio: 'inherit' });
            } catch (err) {
              // Ignore errors if migration is already applied
              console.log(`[Baseline Check] Migration ${migration} already applied or skipped.`);
            }
          }
        }
      }
    } catch (e) {
      console.error("[Baseline Check] Error connecting to database:", e.message);
    } finally {
      await client.end();
    }
  }

  console.log("Starting prisma migrate deploy...");
  try {
    execSync(`npx prisma migrate deploy --schema ${schemaPath}`, { stdio: 'inherit' });
  } catch (error) {
    console.error("Error during prisma migrate deploy:", error.message);
    process.exit(1);
  }
}

main().catch(console.error);
