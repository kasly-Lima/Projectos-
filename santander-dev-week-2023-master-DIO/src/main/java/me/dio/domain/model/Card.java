package me.dio.domain.model;

// Importa as classes necessárias do Jakarta Persistence
import jakarta.persistence.*;

import java.math.BigDecimal;

// Anotação que indica que esta classe é uma entidade JPA
@Entity(name = "tb_card") // Nome da tabela no banco de dados
public class Card {

    @Id // Indica que este campo é a chave primária da entidade
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Configura a geração automática de valores da chave primária
    private Long id; // Identificador único do cartão

    @Column(unique = true) // Indica que o número do cartão deve ser único
    private String number; // Número do cartão

    @Column(name = "available_limit", precision = 13, scale = 2) // Define o nome da coluna e a precisão e escala para o limite
    private BigDecimal limit; // Limite disponível no cartão

    // Método getter para obter o ID do cartão
    public Long getId() {
        return id;
    }

    // Método setter para definir o ID do cartão
    public void setId(Long id) {
        this.id = id;
    }

    // Método getter para obter o número do cartão
    public String getNumber() {
        return number;
    }

    // Método setter para definir o número do cartão
    public void setNumber(String number) {
        this.number = number;
    }

    // Método getter para obter o limite do cartão
    public BigDecimal getLimit() {
        return limit;
    }

    // Método setter para definir o limite do cartão
    public void setLimit(BigDecimal limit) {
        this.limit = limit;
    }

}
