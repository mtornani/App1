#!/usr/bin/env node
// Genera una chiave di licenza ScoutPad PRO per l'email dell'acquirente.
// Il secret DEVE coincidere con LICENSE_SECRET in app.js (cambialo in entrambi
// prima di vendere). Uso:
//   SCOUTPAD_SECRET=il-tuo-secret node tools/genkey.js cliente@email.it
import { createHmac } from 'node:crypto';

const email = process.argv[2];
if (!email) {
  console.error('Uso: node tools/genkey.js <email-acquirente>');
  process.exit(1);
}
const secret = process.env.SCOUTPAD_SECRET || 'scoutpad-change-me';
const hex = createHmac('sha256', secret)
  .update(email.trim().toLowerCase())
  .digest('hex')
  .slice(0, 16)
  .toUpperCase();
console.log(`Email:   ${email.trim().toLowerCase()}`);
console.log(`Licenza: ${hex.match(/.{4}/g).join('-')}`);
if (secret === 'scoutpad-change-me') {
  console.error('\nATTENZIONE: stai usando il secret di default. Cambialo (env SCOUTPAD_SECRET + LICENSE_SECRET in app.js) prima di vendere.');
}
