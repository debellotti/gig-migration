package com.example;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Component
public class TransactionConsumer {

    private static final Logger log = LoggerFactory.getLogger(TransactionConsumer.class);

    private final TransactionRepository repository;

    public TransactionConsumer(TransactionRepository repository) {
        this.repository = repository;
    }

    @KafkaListener(topics = "transactions", groupId = "transactions-group")
    public void consume(ConsumerRecord<String, String> record) {
        log.info("Consumed partition={} offset={}", record.partition(), record.offset());
        try {
            // SplitText sends header+data; take the last non-empty line
            String[] lines = record.value().strip().split("\n");
            String csv = lines[lines.length - 1].strip();

            String[] cols = csv.split(",");
            if (cols.length < 6) {
                log.warn("Skipping malformed record at offset={}", record.offset());
                return;
            }

            Transaction tx = new Transaction();
            tx.setTransactionId(cols[0].trim());
            tx.setAccountId(cols[1].trim());
            tx.setAmount(new BigDecimal(cols[2].trim()));
            tx.setCurrency(cols[3].trim());
            tx.setTs(OffsetDateTime.parse(cols[4].trim()));
            tx.setStatus(cols[5].trim());

            repository.save(tx);
            log.info("Persisted transaction {}", tx.getTransactionId());
        } catch (Exception e) {
            log.error("Failed to process record at offset={}: {}", record.offset(), e.getMessage());
        }
    }
}
