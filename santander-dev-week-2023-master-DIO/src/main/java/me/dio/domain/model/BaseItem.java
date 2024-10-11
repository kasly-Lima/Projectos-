package me.dio.domain.model;

// Importa as classes necessárias do Jakarta Persistence
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;

// Anotação que indica que esta classe é uma superclasse mapeada
@MappedSuperclass // Classes que herdam desta classe não terão uma tabela própria, mas herdarão os atributos
public abstract class BaseItem {

    @Id // Indica que este campo é a chave primária da entidade
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Configura a geração automática de valores da chave primária
    private Long id; // Identificador único do item

    private String icon; // Ícone associado ao item

    private String description; // Descrição do item

    // Método getter para obter o ID do item
    public Long getId() {
        return id;
    }

    // Método setter para definir o ID do item
    public void setId(Long id) {
        this.id = id;
    }

    // Método getter para obter o ícone do item
    public String getIcon() {
        return icon;
    }

    // Método setter para definir o ícone do item
    public void setIcon(String icon) {
        this.icon = icon;
    }

    // Método getter para obter a descrição do item
    public String getDescription() {
        return description;
    }

    // Método setter para definir a descrição do item
    public void setDescription(String description) {
        this.description = description;
    }

}
