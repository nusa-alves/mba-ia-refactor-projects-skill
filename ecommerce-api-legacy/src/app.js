'use strict';

const express = require('express');
const settings = require('./config/settings');
const { createDatabase } = require('./database/connection');
const { initializeDatabase } = require('./database/initialize');
const { buildRoutes } = require('./routes');
const { errorHandler } = require('./middlewares/errorHandler');
const { logEvent } = require('./middlewares/logger');

function createApp({ db, appSettings }) {
    const app = express();
    app.use(express.json());
    app.use(buildRoutes({ db, settings: appSettings }));
    app.use(errorHandler);
    return app;
}

async function start() {
    const db = createDatabase(settings.dbPath);
    await initializeDatabase(db, settings.seedUserPassword);
    const app = createApp({ db, appSettings: settings });
    return app.listen(settings.port, () => {
        logEvent('server_started', { port: settings.port });
    });
}

if (require.main === module) {
    start().catch((error) => {
        process.stderr.write(`${JSON.stringify({ level: 'error', message: error.message })}\n`);
        process.exitCode = 1;
    });
}

module.exports = { createApp, start };
