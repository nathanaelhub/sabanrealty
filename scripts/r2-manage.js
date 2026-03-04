/**
 * Cloudflare R2 Management Script
 * Usage:
 *   node scripts/r2-manage.js list [prefix]
 *   node scripts/r2-manage.js delete <key>
 *   node scripts/r2-manage.js delete-folder <folder/>
 */

require('dotenv').config();
const { S3Client, ListObjectsV2Command, DeleteObjectCommand, DeleteObjectsCommand } = require('@aws-sdk/client-s3');

const client = new S3Client({
  region: 'auto',
  endpoint: `https://${process.env.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
  },
});

const BUCKET = process.env.CLOUDFLARE_R2_BUCKET;

async function listObjects(prefix = '') {
  const command = new ListObjectsV2Command({
    Bucket: BUCKET,
    Prefix: prefix,
    MaxKeys: 100,
  });
  const response = await client.send(command);
  return response.Contents || [];
}

async function deleteObject(key) {
  const command = new DeleteObjectCommand({
    Bucket: BUCKET,
    Key: key,
  });
  await client.send(command);
  console.log(`Deleted: ${key}`);
}

async function deleteFolder(prefix) {
  const objects = await listObjects(prefix);
  if (objects.length === 0) {
    console.log(`No objects found with prefix: ${prefix}`);
    return;
  }

  const deleteCommand = new DeleteObjectsCommand({
    Bucket: BUCKET,
    Delete: {
      Objects: objects.map(obj => ({ Key: obj.Key })),
    },
  });

  const response = await client.send(deleteCommand);
  console.log(`Deleted ${response.Deleted?.length || 0} objects from ${prefix}`);
}

async function main() {
  const [,, action, ...args] = process.argv;

  try {
    switch (action) {
      case 'list':
        const prefix = args[0] || '';
        const objects = await listObjects(prefix);
        if (objects.length === 0) {
          console.log('No objects found');
        } else {
          objects.forEach(obj => console.log(`${obj.Key} (${obj.Size} bytes)`));
        }
        break;

      case 'delete':
        if (!args[0]) {
          console.error('Please provide a key to delete');
          process.exit(1);
        }
        await deleteObject(args[0]);
        break;

      case 'delete-folder':
        if (!args[0]) {
          console.error('Please provide a folder prefix to delete');
          process.exit(1);
        }
        await deleteFolder(args[0]);
        break;

      default:
        console.log('R2 Management Script');
        console.log('Usage:');
        console.log('  node scripts/r2-manage.js list [prefix]     - List objects');
        console.log('  node scripts/r2-manage.js delete <key>      - Delete single object');
        console.log('  node scripts/r2-manage.js delete-folder <prefix>  - Delete all objects with prefix');
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

main();
