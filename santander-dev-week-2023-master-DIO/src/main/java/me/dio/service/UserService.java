package me.dio.service;

// Importa a classe User do modelo de domínio
import me.dio.domain.model.User;

// Interface que define os serviços relacionados à entidade User
public interface UserService {

    // Método para encontrar um usuário pelo ID
    User findById(Long id);

    // Método para criar um novo usuário
    User create(User userToCreate);
}
