const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

async function main() {
  const provider = process.env.DATABASE_PROVIDER || 'postgresql';
  // Capture the original command from arguments, e.g., "rm -rf ... && npx prisma migrate deploy ..."
  let commandArgs = process.argv.slice(2).join(' ');

  if (commandArgs) {
    commandArgs = commandArgs.replace(/DATABASE_PROVIDER/g, provider);
  }

  console.log(`[runWithProvider] Starting with provider: ${provider}`);

  if (provider === 'postgresql' && process.env.DATABASE_URL) {
    const client = new Client({ connectionString: process.env.DATABASE_URL });
    try {
      await client.connect();
      
      // Step 1: Check if the _prisma_migrations table exists
      const res = await client.query(`
        SELECT EXISTS (
          SELECT FROM information_schema.tables 
          WHERE table_schema = 'public' 
          AND table_name = '_prisma_migrations'
        );
      `);
      
      const migrationsTableExists = res.rows[0].exists;

      // Check if there are actual tables in the DB to determine if it's populated
      const tablesRes = await client.query(`
        SELECT count(*) as count FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name != '_prisma_migrations';
      `);
      const hasOtherTables = parseInt(tablesRes.rows[0].count, 10) > 0;

      // Only baseline if the database already has tables (otherwise it's fresh and deploy works fine)
      if (hasOtherTables) {
        console.log("[Baseline] Database is not empty. Checking if we need to resolve existing migrations...");
        
        // Ensure migrations folder is ready to be used by resolve
        const migrationsSourceDir = path.join(__dirname, 'prisma', `${provider}-migrations`);
        const migrationsTargetDir = path.join(__dirname, 'prisma', 'migrations');
        const schemaPath = path.join(__dirname, 'prisma', `${provider}-schema.prisma`);
        
        if (fs.existsSync(migrationsSourceDir)) {
          // Copy migrations just like the original script does, so we can run resolve
          if (fs.existsSync(migrationsTargetDir)) {
            fs.rmSync(migrationsTargetDir, { recursive: true, force: true });
          }
          fs.cpSync(migrationsSourceDir, migrationsTargetDir, { recursive: true });
          
          const migrations = fs.readdirSync(migrationsTargetDir)
            .filter(file => fs.statSync(path.join(migrationsTargetDir, file)).isDirectory())
            .sort();
          
          for (const migration of migrations) {
            try {
              // Try to resolve the migration. If it's already applied or doesn't need it, Prisma will skip/error safely.
              execSync(`npx prisma migrate resolve --applied "${migration}" --schema ${schemaPath}`, { stdio: 'ignore' });
              console.log(`[Baseline] Resolved migration: ${migration}`);
            } catch (err) {
              // Ignore failure (usually means it's already applied)
            }
          }
          console.log("[Baseline] Finished baselining all existing migrations.");
        } else {
          console.warn(`[Baseline] Migrations directory not found at ${migrationsSourceDir}`);
        }
      } else {
        console.log("[Baseline] Database is empty. Proceeding normally without baselining.");
      }
    } catch (e) {
      console.error("[Baseline] Error connecting to database:", e.message);
    } finally {
      await client.end();
    }
  }

  // Execute the original intended command
  if (commandArgs) {
    console.log(`[runWithProvider] Executing original command: ${commandArgs}`);
    try {
      execSync(commandArgs, { stdio: 'inherit' });
    } catch (err) {
      console.error("[runWithProvider] Error executing original command.");
      process.exit(1);
    }
  } else {
    console.log("[runWithProvider] No command passed to execute.");
  }
}

main().catch(console.error);
