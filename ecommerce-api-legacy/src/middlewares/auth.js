'use strict';

const { timingSafeEqual } = require('node:crypto');

function requireAdmin({ adminToken }) {
    return function authenticateAdmin(req, res, next) {
        const providedToken = req.get('X-Admin-Token') || '';
        const expected = Buffer.from(adminToken);
        const provided = Buffer.from(providedToken);
        if (expected.length === 0 || expected.length !== provided.length
            || !timingSafeEqual(expected, provided)) {
            return res.status(403).json({ erro: 'Acesso negado' });
        }
        next();
    };
}

module.exports = { requireAdmin };
