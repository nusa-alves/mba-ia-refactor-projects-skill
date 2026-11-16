'use strict';

class AppError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

function errorHandler(error, req, res, next) {
    if (res.headersSent) return next(error);
    const knownAppError = error instanceof AppError;
    const malformedBody = !knownAppError && error.status === 400;
    const status = knownAppError ? error.status : (malformedBody ? 400 : 500);
    if (status >= 500) {
        process.stderr.write(`${JSON.stringify({ level: 'error', message: error.message })}\n`);
    }
    const message = knownAppError
        ? error.message
        : (malformedBody ? 'Bad Request' : 'Erro interno do servidor');
    res.status(status).send(message);
}

module.exports = { AppError, errorHandler };
