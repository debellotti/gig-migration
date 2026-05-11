package com.example;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "accounts")
@Getter @Setter @NoArgsConstructor
public class Account {

    @Id @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;
    private String ownerName;
    @Column(precision = 19, scale = 4)
    private BigDecimal balance;
    @Column(length = 3)
    private String currency;
    private OffsetDateTime createdAt = OffsetDateTime.now();
}
