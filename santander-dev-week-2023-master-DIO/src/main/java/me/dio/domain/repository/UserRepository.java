package me.dio.domain.repository;

// Importa as classes necessárias para a interface JpaRepository e a anotação Repository
import me.dio.domain.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

// Anotação que indica que esta interface é um repositório do Spring
@Repository
public interface UserRepository extends JpaRepository<User, Long> { // Extende JpaRepository para operações CRUD

    // Método para verificar se um número de conta já existe no banco de dados
    boolean existsByAccountNumber(String accountNumber);
}
