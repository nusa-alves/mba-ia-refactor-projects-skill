'use strict';

const CARD_LOG_SUFFIX_LENGTH = 4;

function logEvent(event, fields = {}) {
    process.stdout.write(`${JSON.stringify({ level: 'info', event, ...fields })}\n`);
}

module.exports = { logEvent, CARD_LOG_SUFFIX_LENGTH };
