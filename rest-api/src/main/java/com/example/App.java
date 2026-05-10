package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class App {

    private final KafkaTemplate<String, String> kafka;

    public App(KafkaTemplate<String, String> kafka) {
        this.kafka = kafka;
    }

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }

    @GetMapping("/")
    public String ciao() {
        return "ciao";
    }

    @PostMapping("/send")
    public String send(@RequestBody String message) {
        kafka.send("ciao-topic", message);
        return "inviato: " + message;
    }
}
