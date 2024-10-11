package me.dio.domain.model;

// Importa as classes necessárias do Jakarta Persistence
import jakarta.persistence.*;

import java.math.BigDecimal;

// Anotação que indica que esta classe é uma entidade JPA
@Entity(name = "tb_account") // Nome da tabela no banco de dados
public class Account {

    @Id // Indica que este campo é a chave primária da entidade
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Configura a geração automática de valores da chave primária
    private Long id; // Identificador único da conta

    @Column(unique = true) // Indica que o número da conta deve ser único
    private String number; // Número da conta

    private String agency; // Agência da conta

    @Column(precision = 13, scale = 2) // Define a precisão e a escala para o saldo
    private BigDecimal balance; // Saldo atual da conta

    @Column(name = "additional_limit", precision = 13, scale = 2) // Define o nome da coluna e a precisão e escala para o limite
    private BigDecimal limit; // Limite adicional da conta

    // Método getter para obter o ID da conta
    public Long getId() {
        return id;
    }

    // Método setter para definir o ID da conta
    public void setId(Long id) {
        this.id = id;
    }

    // Método getter para obter o número da conta
    public String getNumber() {
        return number;
    }

    // Método setter para definir o número da conta
    public void setNumber(String number) {
        this.number = number;
    }

    // Método getter para obter a agência da conta
    public String getAgency() {
        return agency;
    }

    // Método setter para definir a agência da conta
    public void setAgency(String agency) {
        this.agency = agency;
    }

    // Método getter para obter o saldo da conta
    public BigDecimal getBalance() {
        return balance;
    }

    // Método setter para definir o saldo da conta
    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    // Método getter para obter o limite adicional da conta
    public BigDecimal getLimit() {
        return limit;
    }

    // Método setter para definir o limite adicional da conta
    public void setLimit(BigDecimal limit) {
        this.limit = limit;
    }

}
