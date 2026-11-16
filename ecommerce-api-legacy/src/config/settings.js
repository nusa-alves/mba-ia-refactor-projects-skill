'use strict';

module.exports = Object.freeze({
    port: Number(process.env.PORT || 3000),
    dbPath: process.env.DB_PATH || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || '',
    seedUserPassword: process.env.SEED_USER_PASSWORD || ''
});
