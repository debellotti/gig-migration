package com.example;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "transfers")
@Getter @Setter @NoArgsConstructor
public class Transfer {

    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private UUID fromAccountId;
    private UUID toAccountId;
    @Column(precision = 19, scale = 4)
    private BigDecimal amount;
    @Column(length = 3)
    private String currency;
    private OffsetDateTime createdAt = OffsetDateTime.now();
}
