package com.example;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
public class AccountController {

    private final AccountRepository accounts;
    private final TransferRepository transfers;
    private final TransferService transferService;

    record CreateAccountRequest(String ownerName, String currency, BigDecimal initialBalance) {}
    record TransferRequest(UUID fromAccountId, UUID toAccountId, BigDecimal amount) {}

    @PostMapping("/accounts")
    @ResponseStatus(HttpStatus.CREATED)
    Account create(@RequestBody CreateAccountRequest req) {
        Account a = new Account();
        a.setOwnerName(req.ownerName());
        a.setCurrency(req.currency().toUpperCase());
        a.setBalance(req.initialBalance());
        return accounts.save(a);
    }

    @GetMapping("/accounts/{id}")
    Account get(@PathVariable UUID id) {
        return accounts.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }

    @PostMapping("/transfers")
    @ResponseStatus(HttpStatus.CREATED)
    Transfer transfer(@RequestBody TransferRequest req) {
        return transferService.execute(req.fromAccountId(), req.toAccountId(), req.amount());
    }

    @GetMapping("/accounts/{id}/transfers")
    List<Transfer> history(@PathVariable UUID id) {
        return transfers.findByFromAccountIdOrToAccountId(id, id);
    }
}
