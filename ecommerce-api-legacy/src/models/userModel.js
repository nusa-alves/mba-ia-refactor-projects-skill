'use strict';

const crypto = require('node:crypto');
const { timingSafeEqual } = require('node:crypto');
const { get, run } = require('../database/connection');

const PASSWORD_SALT_BYTES = 16;
const PASSWORD_KEY_BYTES = 64;

function hashPassword(password) {
    const salt = crypto.randomBytes(PASSWORD_SALT_BYTES);
    return new Promise((resolve, reject) => {
        crypto.scrypt(password, salt, PASSWORD_KEY_BYTES, (error, derivedKey) => {
            if (error) return reject(error);
            resolve(`scrypt$${salt.toString('hex')}$${derivedKey.toString('hex')}`);
        });
    });
}

function derivePassword(password, salt, length) {
    return new Promise((resolve, reject) => {
        crypto.scrypt(password, salt, length, (error, derivedKey) => {
            if (error) return reject(error);
            resolve(derivedKey);
        });
    });
}

async function findByEmail(db, email) {
    return get(db, 'SELECT id, name, email, pass AS passwordHash FROM users WHERE email = ?', [email]);
}

async function verifyPassword(db, user, password) {
    const parts = user.passwordHash.split('$');
    if (parts.length !== 3 || parts[0] !== 'scrypt') {
        if (user.passwordHash !== password) return false;
        const migratedHash = await hashPassword(password);
        await run(db, 'UPDATE users SET pass = ? WHERE id = ?', [migratedHash, user.id]);
        return true;
    }

    const salt = Buffer.from(parts[1], 'hex');
    const expectedHash = Buffer.from(parts[2], 'hex');
    if (salt.length !== PASSWORD_SALT_BYTES || expectedHash.length !== PASSWORD_KEY_BYTES) return false;
    const actualHash = await derivePassword(password, salt, PASSWORD_KEY_BYTES);
    return timingSafeEqual(expectedHash, actualHash);
}

async function create(db, { name, email, password }) {
    const passwordHash = await hashPassword(password);
    return run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passwordHash]);
}

async function remove(db, userId) {
    return run(db, 'DELETE FROM users WHERE id = ?', [userId]);
}

module.exports = { findByEmail, create, remove, hashPassword, verifyPassword };
