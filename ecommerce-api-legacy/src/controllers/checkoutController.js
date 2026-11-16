'use strict';

const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const checkoutModel = require('../models/checkoutModel');
const asyncHandler = require('./asyncHandler');
const { AppError } = require('../middlewares/errorHandler');
const { logEvent, CARD_LOG_SUFFIX_LENGTH } = require('../middlewares/logger');
const paymentStatusValues = require('../models/paymentStatus');

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function createCheckoutController({ db }) {
    return {
        checkout: asyncHandler(async (req, res) => {
            const { usr: userName, eml: email, pwd: password, c_id: courseId, card } = req.body || {};
            if (typeof userName !== 'string' || !userName.trim()
                || typeof email !== 'string' || !isValidEmail(email)
                || typeof password !== 'string' || !password || password.length > 256
                || !Number.isInteger(Number(courseId)) || Number(courseId) <= 0
                || typeof card !== 'string' || !/^\d{12,19}$/.test(card)) {
                throw new AppError('Bad Request', 400);
            }

            let course;
            try {
                course = await courseModel.findActiveById(db, Number(courseId));
            } catch {
                throw new AppError('Erro DB', 500);
            }
            if (!course) throw new AppError('Curso não encontrado', 404);

            let user;
            try {
                user = await userModel.findByEmail(db, email);
            } catch {
                throw new AppError('Erro ao criar usuário', 500);
            }
            if (user) {
                let passwordMatches;
                try {
                    passwordMatches = await userModel.verifyPassword(db, user, password);
                } catch {
                    throw new AppError('Erro ao criar usuário', 500);
                }
                if (!passwordMatches) throw new AppError('Credenciais inválidas', 401);
            } else {
                try {
                    const created = await userModel.create(db, { name: userName, email, password });
                    user = { id: created.lastID };
                } catch {
                    throw new AppError('Erro ao criar usuário', 500);
                }
            }

            const paymentStatus = paymentStatusValues.statusForCard(card);
            logEvent('payment_processing', { last4: card.slice(-CARD_LOG_SUFFIX_LENGTH) });
            if (paymentStatus === paymentStatusValues.DENIED) {
                throw new AppError('Pagamento recusado', 400);
            }

            let enrollmentId;
            try {
                enrollmentId = await checkoutModel.complete(db, {
                    userId: user.id,
                    courseId: Number(courseId),
                    course,
                    status: paymentStatus
                });
            } catch {
                throw new AppError('Erro Pagamento', 500);
            }

            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        })
    };
}

module.exports = { createCheckoutController };
