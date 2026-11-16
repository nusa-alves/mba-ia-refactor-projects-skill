'use strict';

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED'
});

const APPROVED_CARD_PREFIX = '4';

function statusForCard(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX)
        ? PAYMENT_STATUS.PAID
        : PAYMENT_STATUS.DENIED;
}

module.exports = { ...PAYMENT_STATUS, statusForCard };
