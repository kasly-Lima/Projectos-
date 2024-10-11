package me.dio.domain.model;

// Importa as classes necessárias do Jakarta Persistence
import jakarta.persistence.Entity;

// Anotação que indica que esta classe é uma entidade JPA
@Entity(name = "tb_news") // Nome da tabela no banco de dados
public class News extends BaseItem { // Extende a classe BaseItem para herdar seus atributos

    // Esta classe não possui atributos ou métodos adicionais
    // Ela herda os atributos id, icon e description da classe BaseItem
}
