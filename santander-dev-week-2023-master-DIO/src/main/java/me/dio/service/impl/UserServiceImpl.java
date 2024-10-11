package me.dio.service.impl;

// Importa as classes necessárias para a implementação do serviço UserService
import me.dio.domain.model.User;
import me.dio.domain.repository.UserRepository;
import me.dio.service.UserService;
import org.springframework.stereotype.Service;

import java.util.NoSuchElementException;

// Anotação que indica que esta classe é um serviço do Spring
@Service
public class UserServiceImpl implements UserService { // Implementa a interface UserService

    private final UserRepository userRepository; // Repositório de usuários para operações de banco de dados

    // Construtor que injeta a dependência do repositório de usuários
    public UserServiceImpl(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public User findById(Long id) {
        // Busca um usuário pelo ID e lança uma exceção se não for encontrado
        return userRepository.findById(id).orElseThrow(NoSuchElementException::new);
    }

    @Override
    public User create(User userToCreate) {
        // Verifica se o número da conta já existe no repositório
        if (userRepository.existsByAccountNumber(userToCreate.getAccount().getNumber())) {
            throw new IllegalArgumentException("This Account number already exists."); // Lança exceção se existir
        }
        // Salva o novo usuário no repositório e retorna o usuário criado
        return userRepository.save(userToCreate);
    }
}
