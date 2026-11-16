'use strict';

const userModel = require('../models/userModel');
const asyncHandler = require('./asyncHandler');
const { AppError } = require('../middlewares/errorHandler');

function createUserController({ db }) {
    return {
        remove: asyncHandler(async (req, res) => {
            const userId = Number(req.params.id);
            if (!Number.isInteger(userId) || userId <= 0) {
                throw new AppError('Bad Request', 400);
            }
            try {
                await userModel.remove(db, userId);
            } catch {
                throw new AppError('Erro DB', 500);
            }
            res.send('Usuário deletado, matrículas e pagamentos relacionados removidos.');
        })
    };
}

module.exports = { createUserController };
