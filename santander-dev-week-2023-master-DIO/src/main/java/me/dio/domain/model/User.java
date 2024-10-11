package me.dio.domain.model;

// Importa as classes necessárias do Jakarta Persistence e List
import jakarta.persistence.*;
import java.util.List;

// Anotação que indica que esta classe é uma entidade JPA
@Entity(name = "tb_user") // Nome da tabela no banco de dados
public class User {

    @Id // Indica que este campo é a chave primária da entidade
    @GeneratedValue(strategy = GenerationType.IDENTITY) // Configura a geração automática de valores da chave primária
    private Long id; // Identificador único do usuário

    private String name; // Nome do usuário

    @OneToOne(cascade = CascadeType.ALL) // Relacionamento de um-para-um com a entidade Account
    private Account account; // Conta associada ao usuário

    @OneToOne(cascade = CascadeType.ALL) // Relacionamento de um-para-um com a entidade Card
    private Card card; // Cartão associado ao usuário

    @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER) // Relacionamento de um-para-muitos com a entidade Feature
    private List<Feature> features; // Lista de características associadas ao usuário

    @OneToMany(cascade = CascadeType.ALL, fetch = FetchType.EAGER) // Relacionamento de um-para-muitos com a entidade News
    private List<News> news; // Lista de notícias associadas ao usuário

    // Método getter para obter o ID do usuário
    public Long getId() {
        return id;
    }

    // Método setter para definir o ID do usuário
    public void setId(Long id) {
        this.id = id;
    }

    // Método getter para obter o nome do usuário
    public String getName() {
        return name;
    }

    // Método setter para definir o nome do usuário
    public void setName(String name) {
        this.name = name;
    }

    // Método getter para obter a conta associada ao usuário
    public Account getAccount() {
        return account;
    }

    // Método setter para definir a conta associada ao usuário
    public void setAccount(Account account) {
        this.account = account;
    }

    // Método getter para obter o cartão associado ao usuário
    public Card getCard() {
        return card;
    }

    // Método setter para definir o cartão associado ao usuário
    public void setCard(Card card) {
        this.card = card;
    }

    // Método getter para obter a lista de características associadas ao usuário
    public List<Feature> getFeatures() {
        return features;
    }

    // Método setter para definir a lista de características associadas ao usuário
    public void setFeatures(List<Feature> features) {
        this.features = features;
    }

    // Método getter para obter a lista de notícias associadas ao usuário
    public List<News> getNews() {
        return news;
    }

    // Método setter para definir a lista de notícias associadas ao usuário
    public void setNews(List<News> news) {
        this.news = news;
    }

}
