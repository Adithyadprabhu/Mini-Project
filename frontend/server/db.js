import { DatabaseSync } from 'node:sqlite';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DB_PATH = path.join(__dirname, 'sentinel.db');

export const db = new DatabaseSync(DB_PATH);

// Initialize schema
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    badge_number TEXT,
    phone TEXT,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS sos_requests (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT,
    user_phone TEXT,
    latitude REAL,
    longitude REAL,
    location_name TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    assigned_unit TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    priority TEXT NOT NULL,
    severity INTEGER NOT NULL,
    location TEXT NOT NULL,
    zone TEXT NOT NULL,
    threat TEXT,
    unit TEXT,
    dispatched INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'OPEN',
    sos_id TEXT,
    created_at TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS geofence_alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
  );
`);

// Password utilities
export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return { salt, hash };
}

export function verifyPassword(password, salt, expectedHash) {
  try {
    const hash = crypto.scryptSync(password, salt, 64).toString('hex');
    return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), Buffer.from(expectedHash, 'hex'));
  } catch {
    return false;
  }
}

// Seed default administrative and tactical patrol accounts if not existing
function seedDefaultAccounts() {
  const checkUser = db.prepare('SELECT id FROM users WHERE email = ?');

  // Admin Account
  const adminEmail = process.env.ADMIN_EMAIL || 'admin@yourdomain.com';
  const existingAdmin = checkUser.get(adminEmail);
  if (!existingAdmin) {
    const { salt, hash } = hashPassword(process.env.ADMIN_PASSWORD || 'Admin@Sentinel2026!');
    db.prepare(`
      INSERT INTO users (id, email, password_hash, salt, role, name, created_at)
      VALUES (?, ?, ?, ?, 'admin', 'Command Chief Administrator', ?)
    `).run('usr_admin_01', adminEmail, hash, salt, new Date().toISOString());
  }

  // Police Officer Account
  const policeEmail = process.env.POLICE_EMAIL || 'police@yourdomain.com';
  const existingPolice = checkUser.get(policeEmail);
  if (!existingPolice) {
    const { salt, hash } = hashPassword(process.env.POLICE_PASSWORD || 'Police@Sentinel2026!');
    db.prepare(`
      INSERT INTO users (id, email, password_hash, salt, role, name, badge_number, phone, created_at)
      VALUES (?, ?, ?, ?, 'police', 'Officer J. Vance', 'APD-504', '(404) 658-7054', ?)
    `).run('usr_police_01', policeEmail, hash, salt, new Date().toISOString());
  }
}

seedDefaultAccounts();

// User repository helpers
export function createUser({ email, password, role, name, badgeNumber = null, phone = null }) {
  const id = `usr_${crypto.randomUUID()}`;
  const { salt, hash } = hashPassword(password);
  const now = new Date().toISOString();

  db.prepare(`
    INSERT INTO users (id, email, password_hash, salt, role, name, badge_number, phone, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(id, email.toLowerCase().trim(), hash, salt, role, name.trim(), badgeNumber, phone, now);

  return { id, email: email.toLowerCase().trim(), role, name: name.trim(), badgeNumber, phone };
}

export function getUserByEmail(email) {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email.toLowerCase().trim());
}

export function getUserById(id) {
  return db.prepare('SELECT id, email, role, name, badge_number as badgeNumber, phone, created_at as createdAt FROM users WHERE id = ?').get(id);
}

// Session helpers
export function createSession(userId, role) {
  const token = `tok_${crypto.randomBytes(32).toString('hex')}`;
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(); // 7 days

  db.prepare(`
    INSERT INTO sessions (token, user_id, role, expires_at, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(token, userId, role, expiresAt, now.toISOString());

  return { token, expiresAt };
}

export function validateSession(token) {
  if (!token) return null;
  const session = db.prepare(`
    SELECT s.*, u.email, u.name, u.badge_number as badgeNumber, u.phone
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.token = ? AND datetime(s.expires_at) > datetime('now')
  `).get(token);
  return session || null;
}

export function deleteSession(token) {
  db.prepare('DELETE FROM sessions WHERE token = ?').run(token);
}

// SOS requests
export function createSosRequest({ userId, userName, userPhone, latitude, longitude, locationName, notes }) {
  const sosId = `SOS-${Date.now().toString().slice(-6)}`;
  const now = new Date().toISOString();

  db.prepare(`
    INSERT INTO sos_requests (id, user_id, user_name, user_phone, latitude, longitude, location_name, status, notes, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
  `).run(sosId, userId, userName, userPhone, latitude || null, longitude || null, locationName || 'Atlanta Tourist Corridor', notes || 'Emergency Tourist SOS Request', now, now);

  // Automatically propagate as a Critical P-1 incident in CAD incident queue!
  const incidentId = `#INC-${new Date().getFullYear()}-${sosId.replace('SOS-', '')}`;
  db.prepare(`
    INSERT INTO incidents (id, title, priority, severity, location, zone, threat, dispatched, status, sos_id, created_at)
    VALUES (?, ?, 'critical', 98, ?, 'Zone 5 Tourist Hub', ?, 0, 'OPEN', ?, ?)
  `).run(
    incidentId,
    `TOURIST EMERGENCY SOS ACTIVATED: ${userName || 'Visitor'}`,
    locationName || 'Centennial Olympic Park Hub',
    `Direct SOS Signal from phone ${userPhone || 'Registered Device'}`,
    sosId,
    now
  );

  return { sosId, incidentId, status: 'ACTIVE', createdAt: now };
}

export function getActiveSosRequests() {
  return db.prepare('SELECT * FROM sos_requests ORDER BY datetime(created_at) DESC').all();
}

export function updateSosStatus(sosId, status, assignedUnit = null) {
  const now = new Date().toISOString();
  db.prepare(`
    UPDATE sos_requests
    SET status = ?, assigned_unit = COALESCE(?, assigned_unit), updated_at = ?
    WHERE id = ?
  `).run(status, assignedUnit, now, sosId);

  // Synchronize with incidents
  if (status === 'DISPATCHED') {
    db.prepare('UPDATE incidents SET dispatched = 1, unit = COALESCE(?, unit) WHERE sos_id = ?').run(assignedUnit, sosId);
  } else if (status === 'RESOLVED') {
    db.prepare("UPDATE incidents SET status = 'RESOLVED' WHERE sos_id = ?").run(sosId);
  }
}

// Incidents
export function getAllIncidents() {
  return db.prepare('SELECT * FROM incidents ORDER BY datetime(created_at) DESC').all();
}

export function assignIncident(incidentId, unit) {
  db.prepare('UPDATE incidents SET dispatched = 1, unit = ? WHERE id = ?').run(unit, incidentId);
  // Synchronize with SOS if linked
  const inc = db.prepare('SELECT sos_id FROM incidents WHERE id = ?').get(incidentId);
  if (inc && inc.sos_id) {
    db.prepare("UPDATE sos_requests SET status = 'DISPATCHED', assigned_unit = ?, updated_at = ? WHERE id = ?")
      .run(unit, new Date().toISOString(), inc.sos_id);
  }
}

export function resolveIncident(incidentId) {
  db.prepare("UPDATE incidents SET status = 'RESOLVED' WHERE id = ?").run(incidentId);
  const inc = db.prepare('SELECT sos_id FROM incidents WHERE id = ?').get(incidentId);
  if (inc && inc.sos_id) {
    db.prepare("UPDATE sos_requests SET status = 'RESOLVED', updated_at = ? WHERE id = ?")
      .run(new Date().toISOString(), inc.sos_id);
  }
}

// Geofence alerts
export function createGeofenceAlert({ userId, type, location, description }) {
  const id = `GEO-${Date.now().toString().slice(-6)}`;
  const now = new Date().toISOString();
  db.prepare(`
    INSERT INTO geofence_alerts (id, user_id, type, location, description, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(id, userId, type, location, description, now);
  return { id, type, location, description, createdAt: now };
}

export function getGeofenceAlerts() {
  return db.prepare('SELECT * FROM geofence_alerts ORDER BY datetime(created_at) DESC LIMIT 20').all();
}
