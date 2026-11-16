'use strict';

const crypto = require('node:crypto');
const { run, get } = require('./connection');
const paymentStatus = require('../models/paymentStatus');
const { hashPassword } = require('../models/userModel');

async function initializeDatabase(db, configuredSeedPassword = '') {
    await run(db, 'PRAGMA foreign_keys = ON');
    await run(db, `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        pass TEXT NOT NULL
    )`);
    await run(db, `CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        price REAL NOT NULL,
        active INTEGER NOT NULL
    )`);
    await run(db, `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id)
    )`);
    await run(db, `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL NOT NULL,
        status TEXT NOT NULL
    )`);
    await run(db, `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        created_at DATETIME NOT NULL
    )`);

    const userCount = await get(db, 'SELECT COUNT(*) AS count FROM users');
    let seedUserId;
    if (userCount.count === 0) {
        const seededPassword = await hashPassword(
            configuredSeedPassword || crypto.randomBytes(32).toString('hex'));
        const createdUser = await run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', seededPassword]);
        seedUserId = createdUser.lastID;
    } else {
        const seedUser = await get(db, 'SELECT id FROM users ORDER BY id LIMIT 1');
        seedUserId = seedUser.id;
    }

    const courseCount = await get(db, 'SELECT COUNT(*) AS count FROM courses');
    let seedCourseId;
    if (courseCount.count === 0) {
        await run(db, "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        const seedCourse = await get(db, "SELECT id FROM courses WHERE title = 'Clean Architecture' ORDER BY id LIMIT 1");
        seedCourseId = seedCourse.id;
    } else {
        const seedCourse = await get(db, 'SELECT id FROM courses ORDER BY id LIMIT 1');
        seedCourseId = seedCourse.id;
    }

    const enrollmentCount = await get(db, 'SELECT COUNT(*) AS count FROM enrollments');
    if (enrollmentCount.count === 0) {
        const seedEnrollment = await run(db,
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [seedUserId, seedCourseId]);
        await run(db, 'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [seedEnrollment.lastID, 997.00, paymentStatus.PAID]);
    }
}

module.exports = { initializeDatabase };
