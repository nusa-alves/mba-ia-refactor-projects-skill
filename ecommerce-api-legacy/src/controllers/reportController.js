'use strict';

const courseModel = require('../models/courseModel');
const asyncHandler = require('./asyncHandler');
const { AppError } = require('../middlewares/errorHandler');

function createReportController({ db }) {
    return {
        financialReport: asyncHandler(async (req, res) => {
            try {
                res.json(await courseModel.financialReport(db));
            } catch {
                throw new AppError('Erro DB', 500);
            }
        })
    };
}

module.exports = { createReportController };
