/**
 * Cloudflare R2 Management Script
 * Usage:
 *   node scripts/r2-manage.js list [prefix]
 *   node scripts/r2-manage.js delete <key>
 *   node scripts/r2-manage.js delete-folder <folder/>
 *   node scripts/r2-manage.js upload <localDir> <prefix>
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { S3Client, ListObjectsV2Command, DeleteObjectCommand, DeleteObjectsCommand, PutObjectCommand } = require('@aws-sdk/client-s3');

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

const CONTENT_TYPES = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.mp4': 'video/mp4',
  '.mov': 'video/quicktime',
  '.webm': 'video/webm',
};

function contentType(filename) {
  return CONTENT_TYPES[path.extname(filename).toLowerCase()] || 'application/octet-stream';
}

async function uploadFolder(localDir, prefix) {
  if (!fs.existsSync(localDir)) {
    console.error(`Local directory not found: ${localDir}`);
    process.exit(1);
  }
  const cleanPrefix = prefix.replace(/\/+$/, '');
  const files = fs.readdirSync(localDir)
    .filter(f => f !== '.DS_Store' && fs.statSync(path.join(localDir, f)).isFile());

  if (files.length === 0) {
    console.log(`No files to upload in ${localDir}`);
    return;
  }

  let uploaded = 0;
  for (const file of files) {
    const key = `${cleanPrefix}/${file}`;
    const body = fs.readFileSync(path.join(localDir, file));
    await client.send(new PutObjectCommand({
      Bucket: BUCKET,
      Key: key,
      Body: body,
      ContentType: contentType(file),
    }));
    uploaded++;
    console.log(`  Uploaded: ${key} (${body.length} bytes, ${contentType(file)})`);
  }
  console.log(`Uploaded ${uploaded} file(s) to ${cleanPrefix}/`);
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

      case 'upload':
        if (!args[0] || !args[1]) {
          console.error('Usage: node scripts/r2-manage.js upload <localDir> <prefix>');
          process.exit(1);
        }
        await uploadFolder(args[0], args[1]);
        break;

      default:
        console.log('R2 Management Script');
        console.log('Usage:');
        console.log('  node scripts/r2-manage.js list [prefix]            - List objects');
        console.log('  node scripts/r2-manage.js delete <key>             - Delete single object');
        console.log('  node scripts/r2-manage.js delete-folder <prefix>   - Delete all objects with prefix');
        console.log('  node scripts/r2-manage.js upload <localDir> <prefix> - Upload a folder of files');
    }
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

main();
