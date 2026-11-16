'use strict';

const express = require('express');
const { createCheckoutController } = require('../controllers/checkoutController');
const { createReportController } = require('../controllers/reportController');
const { createUserController } = require('../controllers/userController');
const { requireAdmin } = require('../middlewares/auth');

function buildRoutes({ db, settings }) {
    const router = express.Router();
    const checkoutController = createCheckoutController({ db });
    const reportController = createReportController({ db });
    const userController = createUserController({ db });
    const adminAuth = requireAdmin(settings);

    router.post('/api/checkout', checkoutController.checkout);
    router.get('/api/admin/financial-report', adminAuth, reportController.financialReport);
    router.delete('/api/users/:id', adminAuth, userController.remove);
    return router;
}

module.exports = { buildRoutes };
