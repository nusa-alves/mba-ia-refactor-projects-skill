'use strict';

const { run } = require('../database/connection');

async function complete(db, { userId, courseId, course, status }) {
    await run(db, 'BEGIN IMMEDIATE');
    try {
        const enrollment = await run(db,
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
        await run(db,
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollment.lastID, course.price, status]);
        await run(db,
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [`Checkout curso ${courseId} por ${userId}`]);
        await run(db, 'COMMIT');
        return enrollment.lastID;
    } catch (error) {
        await run(db, 'ROLLBACK');
        throw error;
    }
}

module.exports = { complete };
