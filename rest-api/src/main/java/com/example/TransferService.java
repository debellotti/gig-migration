package com.example;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.util.UUID;

@Service
@Transactional
@RequiredArgsConstructor
public class TransferService {

    private final AccountRepository accounts;
    private final TransferRepository transfers;

    public Transfer execute(UUID fromId, UUID toId, BigDecimal amount) {
        // lock in UUID order to avoid deadlock under concurrent requests
        boolean fromFirst = fromId.compareTo(toId) < 0;
        Account a = findLocked(fromFirst ? fromId : toId);
        Account b = findLocked(fromFirst ? toId : fromId);
        Account from = fromFirst ? a : b;
        Account to   = fromFirst ? b : a;

        if (!from.getCurrency().equals(to.getCurrency()))
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "currency mismatch");
        if (from.getBalance().compareTo(amount) < 0)
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "insufficient balance");

        from.setBalance(from.getBalance().subtract(amount));
        to.setBalance(to.getBalance().add(amount));

        Transfer t = new Transfer();
        t.setFromAccountId(fromId);
        t.setToAccountId(toId);
        t.setAmount(amount);
        t.setCurrency(from.getCurrency());
        return transfers.save(t);
    }

    private Account findLocked(UUID id) {
        return accounts.findByIdWithLock(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "account " + id + " not found"));
    }
}
