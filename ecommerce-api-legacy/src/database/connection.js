'use strict';

const sqlite3 = require('sqlite3').verbose();

function createDatabase(dbPath) {
    return new sqlite3.Database(dbPath);
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(error) {
            if (error) return reject(error);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (error, row) => error ? reject(error) : resolve(row));
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (error, rows) => error ? reject(error) : resolve(rows));
    });
}

module.exports = { createDatabase, run, get, all };
