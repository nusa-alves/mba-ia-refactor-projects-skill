'use strict';

const { get, all } = require('../database/connection');
const paymentStatus = require('./paymentStatus');

async function findActiveById(db, courseId) {
    return get(db, 'SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [courseId]);
}

async function financialReport(db) {
    const rows = await all(db, `
        SELECT courses.id AS course_id,
               courses.title AS course_title,
               enrollments.id AS enrollment_id,
               users.name AS student_name,
               payments.amount AS payment_amount,
               payments.status AS payment_status
        FROM courses
        LEFT JOIN enrollments ON enrollments.course_id = courses.id
        LEFT JOIN users ON users.id = enrollments.user_id
        LEFT JOIN payments ON payments.enrollment_id = enrollments.id
        ORDER BY courses.id, enrollments.id`);

    const courses = new Map();
    for (const row of rows) {
        let course = courses.get(row.course_id);
        if (!course) {
            course = { course: row.course_title, revenue: 0, students: [] };
            courses.set(row.course_id, course);
        }
        if (row.enrollment_id !== null) {
            if (row.payment_status === paymentStatus.PAID) course.revenue += row.payment_amount;
            course.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount ?? 0
            });
        }
    }
    return [...courses.values()];
}

module.exports = { findActiveById, financialReport };
